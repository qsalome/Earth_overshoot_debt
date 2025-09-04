# Ecological debt of humanity: calculation and evolution

Every year since 1971, the [Global Footprint Network](https://www.footprintnetwork.org/)
announces the [Earth Overshoot Day](https://overshoot.footprintnetwork.org/about-earth-overshoot-day/)
which marks the date when humanity starts using more resources than what Earth
can regenerate in that year.

The Earth Overshoot Day is calculated for a given year. However, the excess of
resources consumption does not reset at the end of the year. Instead, it
accumulates in time into an "ecological debt". This project aims at calculating
this "ecological debt", which I define here as the cumulative number of days
after the annual Earth Overshoot Day. If one year, the Earth Overshoot Day is
not reached, then the unused time is deducted from the debt.

## Install

The project is based on Python 3.10. I recommend to use conda and the provided
`environment.yml` file:

    $ conda env create -f environment.yml

## Data and method

The project uses the data of the Global Footprint Network accessible with API.
An API key can be obtained [here](https://data.footprintnetwork.org/#/api).

## Simple example



## Bugs and development

I welcome all changes/ideas/suggestion, big or small, that aim at improving
the projects. Feel free to fork the repository on GitHub and create pull
requests.
Please report any bugs that you find
[here](https://github.com/qsalome/Earth_overshoot_debt/issues).


