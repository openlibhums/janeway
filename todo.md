# To do for ROR integration


- Write a validator on the Affiliation form to check that only one of
author, frozen_author, and preprint_author is present:

```python
def clean(self):
    authorlike_links = set()
    for field in ['account', 'frozen_author', 'preprint_author']:
        if self.cleaned_data.get(field):
            authorlike_links.add(field)
    if len(authorlike_links) > 1:
        raise ValidationError(
            f'Affiliation can only have one of author, ' \
            f'frozen_author, or preprint_author. ' \
            f'Found multiple: { authorlike_links }'
        )

def test_affiliation_clean(self):
    with self.assertRaises(ValidationError):
        self.affiliation_lecturer.frozen_author = self.kathleen_booth_frozen
        self.affiliation_lecturer.clean()
```


- Debug multiple locations being created (e.g. Bathurst, Australia)

- Optimize loading of data, so that the iterations do not slow down the more records are present
