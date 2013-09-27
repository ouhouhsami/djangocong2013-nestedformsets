# Formset imbriqués en Django
**Djangocong 2013 Belfort**, 28/29 Septembre 2013   
Samuel Goldszmidt ([@ouhouhsami](https://twitter.com/ouhouhsami))


1. Les *form*
2. Les *formset*
3. Les *nested formset* (série de formulaires imbriqués)  ... et leur édition simultanée sur une seule page

---

## Les *form*

### Création

#### Class `Form`

Créer un formulaire en spécifiant ses champs.
```
from django import forms

class ContactForm(forms.Form):
    subject = forms.CharField(max_length=100)
    message = forms.CharField()
    sender = forms.EmailField()
    cc_myself = forms.BooleanField(required=False)
```

#### Class `ModelForm`

Créer un formulaire automatiquement à partir d'un modèle Django.
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

### Validation de *form*

```
form = ArticleForm(request.POST)  
# ou
form = ContactForm(request.POST)
if form.is_valid():
   # do something with the form.cleaned_data
```

### Admin - Class `ModelAdmin`

* Edition d'une instance d'un modèle
* Affichage de la liste des instances d'un modèle

```
from django.contrib import admin

class ArticleAdmin(admin.ModelAdmin):
    pass

admin.site.register(Article, ArticleAdmin)
```

---

## Les *formset*

Un "*formset*" est une abstraction qui permet de travailler avec plusieurs formulaires "*form*" sur une même page.

### Création

#### *formset_factory* 
Création de plusieurs instances de `Form`

```
from django.forms.formsets import formset_factory
ContactFormSet = formset_factory(ContactForm)
formset = ContactFormSet()
```

#### *modelformset_factory* 
Création de plusieurs instances de `ModelForm`

```
from django.forms.models import modelformset_factory
ArticleFormSet = modelformset_factory(Article)
formset = ArticleFormSet()
```

#### *inlineformset_factory* 
Création de plusieurs instances de `ModelForm`, liées par une clef étrangère à une même instance.

```
from django.forms.models import inlineformset_factory
ArticleFormSet = inlineformset_factory(Reporter, Article)
reporter = Reporter.objects.get(name=u'Henri Cartier-Bresson')
formset = ArticleFormSet(instance=reporter)
```

### Validation de *formset*

```
formset = ArticleFormSet(request.POST, instance=reporter)
if formset.is_valid():
    # do something with the formset.cleaned_data
    pass
```

### Admin - Class `TabularInline`  `StackedInline`
Permettent d'éditer dans une même page une instance d'un modèle et les instances d'un modèle lié.


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

## Les *nested formset*
  

Partant de ces modèles : `Block` ⇐ `Building` ⇐ `Tenant`

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

> Objectif : Pouvoir éditer les instances de `Building` et les instances imbriquées de `Tenant` dans une seule page.  
> ATTENTION, cela ne fait pas toujours sens en terme d'ergonomie (... mais parfois si).


### Création

> Pas de solution toute faite incluse dans Django (l'admin ne permet d'éditer qu'un niveau de relation).  
> Mais l'approche proposée par Nathan Yergler : [Nested Formsets](http://yergler.net/blog/2013/09/03/nested-formsets-redux/) et [GitHub nested-formset](https://github.com/nyergler/nested-formset) permet d'y remédier.

Une fabrique, en charge de la création du formulaire :

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
    ...
```

La fabrique proposée est semblable à `inlineformset_factory`, mais elle a besoin de 3 modèles, ici `Block`, `Building` et `Tenant` : 

```
def nested_formset_factory(parent_model, child_model, grandchild_model):

    parent_child = inlineformset_factory(
        parent_model,
        child_model,
        formset=BaseNestedFormset,  # <=
    )

    parent_child.nested_formset_class = inlineformset_factory(
        child_model,
        grandchild_model,
    )

    return parent_child
```
2 `inlineformset_factory` : 

* la première construit le formset `BuildingFormset` via `Block` et `Building`
* la seconde construit le formset `TenantFormset` via `Building` et `Tenant`

La première a `BaseNestedFormset` comme paramètre `formset` (en place de `BaseInlineFormSet` par défaut). Cela permet de gérer les formsets `TenantFormset` qui seront liés à chaque form de `BuildingFormset` : 

* Ajouter les `TenantFormset` imbriqués via `add_fields` de `BaseNestedFormset` (dans l'attribut nested de chaque form de `BuildingFormset`)
* Vérifier que les `TenantFormset` imbriqués sont valides via `is_valid`
* Sauvegarder ces `TenantFormset` imbriqués via `save`

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
Basée sur la Class-based view `UpdateView`  

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

Pour l'affichage du formulaire d'édition des `BuildingFormset` et `TenantFormset` imbriqués pour un Block.

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

> BIS REPETITA : ATTENTION, cela fait encore plus rarement sens en terme d'ergonomie (... mais parfois si).

Un cas très imbriqué : cf. [djangocong2013-nestedformsets](https://github.com/ouhouhsami/djangocong2013-nestedformsets)

```
       <= Members
Band   <= Records <= Tracks <= ArtistContribution
       <= Concerts <= TrackPlaylist
```

Début de propositions d'implémentation : 

* Construction d'un graphe de dépendance des modèles
* Construction des formsets associés ((en prenant en compte les relations many2many avec champ supplémentaire))
* Afficher ces formulaires imbriqués via les templates
* Donner la possibilité d'ajouter des séries de formulaires imbriqués en JavaScript



