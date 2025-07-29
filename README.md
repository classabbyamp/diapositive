# diapositive

simple photo gallery generator

install in a venv or similar, then see `diapo --help` for usage.

## configuration

configuration is done in hcl.

the overall config:

```hcl
# where the site will be served
base_url = "https://pics.example.com"
# the title at the top of every page
title = "my cool photos"

# maximum image dimension
image_size = 2000
# max thumbnail size
thumb_size = 512

copyright = {
  artist = "your name here"
  years = "2000-2025"
  licence = "all rights reserved"
}
```

album directories can have their own configuration:

```hcl
# album title: overrides default, which is the slug/id
title = "something"
# cover photo: 1-indexed, overrides default, which is index 1
cover = 2
```
