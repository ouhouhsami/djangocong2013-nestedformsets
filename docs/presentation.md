# Formset imbriqués en Django
**Djangocong 2013 Belfort**, 28/29 Septembre 2013   
Samuel Goldszmidt ([@ouhouhsami](https://twitter.com/ouhouhsami))


1. Les formulaires (*"form"*)
2. Les séries de formulaire (*"formset"*)
3. Les séries de formulaires  (*"formset"*) imbriqués ... et leur édition simultanée sur une seule page

---

## Les formulaires *"form"*

### Création

#### Form

Création d'un formulaire en spécifiant ses champs.
```
from django import forms

class ContactForm(forms.Form):
    subject = forms.CharField(max_length=100)
    message = forms.CharField()
    sender = forms.EmailField()
    cc_myself = forms.BooleanField(required=False)
```

#### ModelForm

Création d'un formulaire automatiquement à partir d'un modèle Django.
```
from django.forms import ModelForm
from django.db import models


class Reporter(models.Model):
    name = models.CharField(max_length=100)


class Article(models.Model):
    pub_date = models.DateField()
    headline = models.CharField(max_length=200)
    content = models.TextField()
    reporter = models.ForeignKey(Reporter)


class ArticleForm(ModelForm):
    class Meta:
        model = Article
        fields = ['pub_date', 'headline', 'content', 'reporter']
```

### Validation

```
form = ArticleForm(request.POST)  
# ou
form = ContactForm(request.POST)
if form.is_valid():
   # do something with the form.cleaned_data
```

### Admin

* Edition d'une instance d'un modèle
* Affichage de la liste des instances d'un modèle

**ModelAdmin**
```
from django.contrib import admin

class ArticleAdmin(admin.ModelAdmin):
    pass

admin.site.register(Article, ArticleAdmin)
```

---

## Les séries de formulaire "*formset*"

Une série de formulaire "*formset*" est une abstraction qui permet de travailler avec plusieurs formulaires sur une même page.

### Création

#### *formset_factory* 
Pour plusieurs instance de Form
```
from django.forms.formsets import formset_factory
ContactFormSet = formset_factory(ContactForm)
formset = ContactFormSet()
```
#### *modelformset_factory* 
Pour plusieurs instances de ModelForm
```
from django.forms.models import modelformset_factory
ArticleFormSet = modelformset_factory(Article)
formset = ArticleFormSet()
```
#### *inlineformset_factory* 
Pour plusieurs instances de ModelForm, liées par clef étrangère à une même instance.
Couche d'abstraction au dessus des séries de formulaires pour un modèle.
```
from django.forms.models import inlineformset_factory
ArticleFormSet = inlineformset_factory(Reporter, Article)
reporter = Reporter.objects.get(name=u'Henri Cartier-Bresson')
formset = BookFormSet(instance=reporter)
```

### Validation

```
formset = ArticleFormSet(request.POST, instance=reporter)
if formset.is_valid():
    # do something with the formset.cleaned_data
    pass
```

### Admin

Edition d'une instance et de ses instances liées par clef étrangère

**TabularInline**, **StackedInline**
```
from django.contrib import admin

class ArticleInline(admin.TabularInline):
    model = Article

class ReporterAdmin(admin.ModelAdmin):
    inlines = [
        ArticleInline,
    ]

admin.site.register(Reporter, ReporterAdmin)
```

## Les séries de formulaires imbriqués
  

Partant de ces modèles : Block <= Building <= Tenant

```
from django.db import models


class Block(models.Model):
    description = models.CharField(max_length=255)


class Building(models.Model):
    block = models.ForeignKey(Block)
    address = models.CharField(max_length=255)


class Tenant(models.Model):
    building = models.ForeignKey(Building)
    name = models.CharField(max_length=255)
    unit = models.CharField(
        blank=False,
        max_length=255,
    )
```

> Objectif : Pouvoir éditer les instances de Building et les instances imbriquées de Tenant dans une seule page.  
> ATTENTION, cela ne fait pas toujours sens en terme d'ergonomie (... mais parfois si).


### Création

> Pas de solution toute faite, mais une approche proposée ici par Nathan Yergler : [Nested Formsets](http://yergler.net/blog/2013/09/03/nested-formsets-redux/) et [GitHub nested-formset](https://github.com/nyergler/nested-formset)

#### Une fabrique

Qui va créer un formulaire du type :

```
    building_form_1
        tenant-building_form_1-form_1
        tenant-building_form_1-form_2
        tenant-building_form_1-form_3
    building_form_2
        tenant-building_form_2-form_1
        tenant-building_form_2-form_2
        tenant-building_form_2-form_3
    building_form_3
        tenant-building_form_3-form_1
        tenant-building_form_3-form_2
        tenant-building_form_3-form_3
```

Equivalente à inlineformset_factory, mais avec les 3 modèles `nested_formset_factory(Block, Building, Tenant)` : 

```
def nested_formset_factory(parent_model, child_model, grandchild_model):

    parent_child = inlineformset_factory(
        parent_model,
        child_model,
        formset=BaseNestedFormset,
    )

    parent_child.nested_formset_class = inlineformset_factory(
        child_model,
        grandchild_model,
    )

    return parent_child
```
BaseNestedFormset comme formset de inlineformset_factory pour Block et Building permet de gérer les formulaires Tenant qui seront liés à chaque Building. Gérer, ie. : 

* ajouter les formulaires
* vérifier qu'ils sont valides
* les sauvegarder

```
from django.forms.models import (
    BaseInlineFormSet,
    inlineformset_factory,
)


class BaseNestedFormset(BaseInlineFormSet):

    def add_fields(self, form, index):

        # allow the super class to create the fields as usual
        super(BaseNestedFormset, self).add_fields(form, index)

        form.nested = self.nested_formset_class(
            instance=form.instance,
            data=form.data if self.is_bound else None,
            prefix='%s-%s' % (
                form.prefix,
                self.nested_formset_class.get_default_prefix(),
            ),
        )

    def is_valid(self):

        result = super(BaseNestedFormset, self).is_valid()

        if self.is_bound:
            # look at any nested formsets, as well
            for form in self.forms:
                result = result and form.nested.is_valid()

        return result

    def save(self, commit=True):

        result = super(BaseNestedFormset, self).save(commit=commit)

        for form in self:
            form.nested.save(commit=commit)

        return result

```



#### Une vue pour l'édition
Basée sur UpdateView Class-based view

```
from django.views.generic.edit import UpdateView

class EditBuildingsView(UpdateView):
    model = models.Block

    def get_template_names(self):

        return ['blocks/building_form.html']

    def get_form_class(self):

        return nested_formset_factory(
            self.model,
            models.Building,
            models.Tenant,
        )

    def get_success_url(self):

        return reverse('blocks-list')

```

#### Le template associé
Pour l'affichage du formulaire d'édition des Buildings et Tenants simultanément pour un Block.
```
<h1>Edit Buildings</h1>

<form action="{% url 'buildings-edit' pk=block.id %}" method="POST">

{% csrf_token %}

{{ form.management_form }}

{% for building in form %}

  {{ building.as_p }}
  {{ building.nested.management_form }}
  {% for tenant in building.nested %}
    {{ tenant.as_p }}
  {% endfor %}

{% endfor %}

<input type="submit" value="Save" />

</form>
```
---

# FIN

---

# Et pour *n* niveaux de profondeurs ?

> BIS REPETITA : ATTENTION, cela fait très très très rarement sens en terme d'ergonomie (... mais parfois si).

Un cas très imbriqué

```
       <= Members
Band   <= Records <= Tracks <= ArtistContribution
       <= Concerts <= TrackPlaylist
```
Le début de propositions d'implémentation : 

* Construire un graphe de dépendance des modèles
* Construire les séries de formulaires associés ((en prenant en compte les relations many2many avec champ supplémentaire))
* Afficher ces formulaires imbriqués via les templates
* Possibilité d'ajouter des séries de formulaires imbriqués en JavaScript

Cf. [djangocong2013-nestedformsets](https://github.com/ouhouhsami/djangocong2013-nestedformsets)

