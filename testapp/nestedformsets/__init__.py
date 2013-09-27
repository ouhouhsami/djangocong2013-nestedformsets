# http://yergler.net/blog/2013/09/03/nested-formsets-redux/

from django.core.exceptions import ValidationError

from django.forms.models import (
    BaseInlineFormSet,
    inlineformset_factory,
)

from django.forms.models import modelform_factory

# Enhanced nested formsets part

class ExtendedBaseNestedFormset(BaseInlineFormSet):

    # more or less the same as BaseNestedFormset
    # except that it allows multiple formset associated with a form

    
    def add_fields(self, form, index):

        # allow the super class to create the fields as usual
        super(ExtendedBaseNestedFormset, self).add_fields(form, index)
        
        form.nested = []
        for nested in self.nested_formset_class:
            form.nested.append(nested(
                instance=form.instance,
                data=form.data if self.is_bound else None,
                prefix='%s-%s' % (
                    form.prefix,
                    nested.get_default_prefix(),)
                )
            )


    def is_valid(self):

        result = super(ExtendedBaseNestedFormset, self).is_valid()
        if self.is_bound:
            # look at any nested formsets, as well
            for form in self.forms:
                if not self._should_delete_form(form):
                    # below we could use is_valid from django.forms.formsets
                    result = result and [f.is_valid() for f in form.nested]

        return result

    def save(self, commit=True):

        result = super(ExtendedBaseNestedFormset, self).save(commit=commit)

        for form in self.forms:
            if not self._should_delete_form(form):
                for f in form.nested:
                    f.save(commit=commit)

        return result


def dep_list(parent_model, dep=None):
    if dep is None: dep = {}
    if parent_model._meta.get_all_related_objects():
        dep[parent_model] = { rel.model for rel in parent_model._meta.get_all_related_objects() }
        for child in dep[parent_model]:
            dep_list(child, dep)
    return dep


def deep_formsets(parent_child, formsets):
    for i, f in enumerate(parent_child):
        if f.model in formsets:
            parent_child[i].nested_formset_class = formsets[f.model]
            deep_formsets(parent_child[i].nested_formset_class, formsets)


def extended_nested_formset_factory(parent_model):
    
    # Build the models dependencies from parent_model {model:set(models), ...}
    dependencies = dep_list(parent_model)

    # Build the formsets associated with involved models {model:set(formsets), ...}
    formsets = {}
    for pm in dependencies:
        for child in dependencies[pm]:
            # Choose the righ formset class: 
            # formset which will have nested formset use ExtendedBaseNestedFormset
            # the others, use regular BaseInlineFormSet
            if child in dependencies: 
                formset = ExtendedBaseNestedFormset
            else:
                formset = BaseInlineFormSet
            # exclude m2m field that have an extra field
            exclude = [m2m.name for m2m in child._meta.many_to_many if not m2m.rel.through._meta.auto_created]
            form = modelform_factory(child, exclude=exclude)
            # append the formset to the related pm
            formsets.setdefault(pm, []).append(inlineformset_factory(pm, child, form=form, formset=formset, extra=1))


    parent_child = formsets[parent_model]
    # [ ConcertFormFormSet, RecordFormFormSet, MembershipFormFormSet ]

    deep_formsets(parent_child, formsets)

    return parent_child

