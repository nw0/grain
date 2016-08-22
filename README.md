# grain
mealy redesign

## Purpose
_grain_ is a meal manager, utilising the Django framework. It should allow a user to track ingredient consumption over many meals, providing a cost estimate for each meal, and reports on inventory levels.

It should be more modular than [Mealy](https://github.com/nw0/mealy/), with reworked calendar and inventory views. Additionally, a firm standpoint should be taken on currency support, with the intention of reducing complexity throughout the project (for instance, the resource type system).

## Requirements
1. [`django-bootstrap3`](https://github.com/dyve/django-bootstrap3) for forms
1. [`django-money`](https://github.com/django-money/django-money/)
