# -*- coding: utf-8 -*-
import elasticsearch_dsl
import elasticsearch
import geopy.geocoders
import geopy.exc
import logging

import pyjobsweb.commands
import pyjobsweb.model
import pyjobsweb.lib


class PopulateESCommand(pyjobsweb.commands.AppContextCommand):
    @staticmethod
    def __handle_insertion_task(job_offer):
        es_job_offer = job_offer.to_elasticsearch_job_offer()

        # Perform the insertion in Elasticsearch
        try:
            # Compute lat, lng of the job offer
            geolocator = geopy.geocoders.Nominatim(timeout=5)
            location = geolocator.geocode(job_offer.address, True)

            if not location:
                raise PopulateESCommand.FailedGeoloc

            es_job_offer.geolocation = [location.longitude, location.latitude]
            es_job_offer.geolocation_error = False
        except (geopy.exc.GeocoderQueryError, PopulateESCommand.FailedGeoloc):
            logging.getLogger(__name__).log(
                logging.WARNING,
                '{}{}{}{}'.format(
                    "Job offer id : ",
                    job_offer.id,
                    " Couldn't compute geolocation of the following address : ",
                    u''.join(job_offer.address).encode('utf-8').strip()
                )
            )
            es_job_offer.geolocation = [0, 0]
            es_job_offer.geolocation_error = True
        except (geopy.exc.GeocoderQuotaExceeded,
                geopy.exc.GeocoderAuthenticationFailure,
                geopy.exc.GeocoderUnavailable,
                geopy.exc.GeocoderNotFound) as e:
            logging.getLogger(__name__).log(
                logging.WARNING,
                '{}{}{}{}{}'.format(
                    "Job offer id : ",
                    job_offer.id,
                    " Error during geolocation : ",
                    e.message,
                    ". Aborting Elasticsearch insertions now..."
                )
            )
            raise PopulateESCommand.AbortException
        except geopy.exc.GeopyError as e:
            logging.getLogger(__name__).log(
                logging.WARNING,
                '{}{}{}{}'.format(
                    "Job offer id : ",
                    job_offer.id,
                    " Error during geolocation : ",
                    e.message
                )
            )

        try:
            # Perform the insertion
            es_job_offer.save()
        except elasticsearch.exceptions.RequestError as e:
            logging.getLogger(__name__).log(
                logging.ERROR,
                '{}{}{}{}{}{}'.format(
                    "Job offer id : ",
                    job_offer.id,
                    ", error during the Elasticsearch insertion : ",
                    e,
                    ".\nInfo : ",
                    e.info
                )
            )
            return

    def take_action(self, parsed_args):
        super(PopulateESCommand, self).take_action(parsed_args)

        job_offers = pyjobsweb.model.JobOfferSQLAlchemy.\
            compute_elasticsearch_pending_insertion()

        for j in job_offers:
            try:
                self.__handle_insertion_task(j)
                # Refresh indices to increase research speed
                elasticsearch_dsl.Index('jobs').refresh()
                # Mark the task as handled so we don't retreat it next time
                pyjobsweb.model.JobOfferSQLAlchemy.\
                    mark_as_inserted_in_elasticsearch(j.id)
            except PopulateESCommand.AbortException:
                return

    class FailedGeoloc(Exception):
        pass

    class AbortException(Exception):
        pass
