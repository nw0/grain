# grain
mealy redesign

## Purpose
_grain_ is a meal manager, utilising the Django framework. It should allow a user to track ingredient consumption over many meals, providing a cost estimate for each meal, and reports on inventory levels.

It should be more modular than [Mealy](https://github.com/nw0/mealy/), with reworked calendar and inventory views. Additionally, a firm standpoint should be taken on currency support, with the intention of reducing complexity throughout the project (for instance, the resource type system).

## Requirements
1. [`django-bootstrap3`](https://github.com/dyve/django-bootstrap3) for forms
1. [`django-money`](https://github.com/django-money/django-money/)
1. `radix`: not publicly available: to reduce `templatetags` duplication. See `nav_active` methods in my other applications.

## Code used
1. [`bootstrap-calendar`](https://github.com/Serhioromano/bootstrap-calendar/). Adapted code and css for use in meal calendar.

## Notes
Anyone implementing _grain_ should pay attention to user authentication and authorisation. This has been left unhandled here, as I am managing it through another application, _radix_. You may wish to require users to be logged in on all views, which should take care of any problems.
