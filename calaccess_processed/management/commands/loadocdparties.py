#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Load OCD Party model from LOOKUP_CODES_CD table in raw CAL-ACCESS data.
"""
import re
from opencivicdata.core.models import Organization
from calaccess_raw.models.common import LookupCodesCd
from calaccess_processed.management.commands import CalAccessCommand


class Command(CalAccessCommand):
    """
    Load OCD Party model from LOOKUP_CODES_CD table in raw CAL-ACCESS data.
    """
    help = 'Load OCD Party model from LOOKUP_CODES_CD table in raw CAL-ACCESS data'

    def add_arguments(self, parser):
        """
        Adds custom arguments specific to this command.
        """
        parser.add_argument(
            "--flush",
            action="store_true",
            dest="flush",
            default=False,
            help="Flush the database tables filled by this command."
        )

    def handle(self, *args, **options):
        """
        Make it happen.
        """
        super(Command, self).handle(*args, **options)
        self.header('Loading Parties')
        if options['flush']:
            self.flush()
        self.load()
        self.success("Done!")

    def flush(self):
        """
        Flush the database tables filled by this command.
        """
        qs = Organization.objects.filter(classification='party')
        if self.verbosity > 0:
            self.log("Flushing {} Organization objects".format(qs.count()))
        qs.delete()

    def load(self):
        """
        Insert Party records from the raw LOOKUP_CODES_CD table.
        """
        # Pull all of the raw LookupCodes in the 16000 code_type series
        # exclude the title entry of "PARTY CODE" with the identical number
        q = LookupCodesCd.objects.filter(code_type=16000).exclude(code_id=16000)

        for lc in q:
            # treat INDEPENDENT and NON-PARTISAN as NO PARTY PREFERENCE
            if lc.code_desc in ['INDEPENDENT', 'NON-PARTISAN']:
                party_name = 'NO PARTY PREFERENCE'
            else:
                party_name = lc.code_desc

            party, created = Organization.objects.get_or_create(
                name=party_name,
                classification='party',
            )
            if created:
                if self.verbosity > 2:
                    self.log(" Created %s" % party)
                # save abbreviation as other party name
                # combine the first char of each word (except AND)
                abbreviation = ''.join(
                    re.findall(
                        r'([A-z])\w+',
                        lc.code_desc.upper().replace(' AND ', '')
                    )
                )
                party.other_names.get_or_create(
                    name=abbreviation,
                    note='abbreviation'
                )

            # keep the code_id too
            p_id, created = party.identifiers.get_or_create(
                scheme='calaccess_lookup_code_id',
                identifier=lc.code_id,
            )
            if created:
                if self.verbosity > 2:
                    self.log(
                        " {0.identifier} indentifies {0.organization.name}".format(p_id)
                    )