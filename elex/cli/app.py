from cement.core.controller import CementBaseController, expose
from cement.core.foundation import CementApp
from cement.ext.ext_logging import LoggingLogHandler
from elex.api import DelegateReport
from elex.api import Elections
from elex.cli.constants import BANNER, LOG_FORMAT
from elex.cli.decorators import require_date_argument, require_ap_api_key
from elex.cli.hooks import add_election_hook, cachecontrol_logging_hook
from shutil import rmtree


class ElexBaseController(CementBaseController):
    class Meta:
        label = 'base'
        description = "Get and process AP elections data"
        arguments = [
            (['date'], dict(
                nargs='*',
                action='store',
                help='Election date (e.g. "2015-11-03"; most common date \
formats accepted).'
            )),
            (['-t', '--test'], dict(
                action='store_true',
                help='Use testing API calls'
            )),
            (['-n', '--not-live'], dict(
                action='store_true',
                help='Do not use live data API calls'
            )),
            (['-d', '--data-file'], dict(
                action='store',
                help='Specify data file instead of making HTTP request when \
using election commands like `elex results` and `elex races`.'
            )),
            (['--delegate-sum-file'], dict(
                action='store',
                help='Specify delegate sum report file instead of making HTTP \
request when using `elex delegates`'
            )),
            (['--delegate-super-file'], dict(
                action='store',
                help='Specify delegate super report file instead of making \
HTTP request when using `elex delegates`'
            )),
            (['--format-json'], dict(
                action='store_true',
                help='Pretty print JSON when using `-o json`.'
            )),
            (['-v', '--version'], dict(
                action='version',
                version=BANNER
            )),
            (['--results-level'], dict(
                action='store',
                help='Specify reporting level for results',
                default='ru'
            )),
            (['--raceids'], dict(
                action='store',
                help='Specify raceids to parse',
                default=[]
            )),
            (['--set-zero-counts'], dict(
                action='store_true',
                help='Override results with zeros; omits the winner indicator.\
Sets the vote, delegate, and reporting precinct counts to zero.',
                default=False
            )),
            (['--national-only'], dict(
                action='store_true',
                help='Limit results to national-level results only.',
                default=None
            )),
            (['--local-only'], dict(
                action='store_true',
                help='Limit results to local-level results only.',
                default=None
            )),
            (['--with-timestamp'], dict(
                action='store_true',
                help='Append a `timestamp` column to each row of data output with current\
                      system timestamp.',
            )),
            (['--batch-name'], dict(
                action='store',
                help='Specify a value for a `batchname` column to append to each row.',
            )),
        ]

    @expose(hide=True)
    def default(self):
        self.app.args.print_help()

    @expose(help="Get races")
    @require_ap_api_key
    @require_date_argument
    def races(self):
        """
        ``elex races <electiondate>``

        Returns race data for a given election date.

        Command:

        .. code:: bash

            elex races 2016-03-26

        Example output:

        .. csv-table::

            id,raceid,racetype,racetypeid,description,electiondate,initialization_data,is_ballot_measure,lastupdated,national,officeid,officename,party,seatname,seatnum,statename,statepostal,test,uncontested
            2919,2919,Caucus,E,,2016-03-26,True,False,2016-03-27T03:03:54Z,True,P,President,Dem,,,,AK,False,False
            12975,12975,Caucus,E,,2016-03-26,True,False,2016-03-29T17:17:41Z,True,P,President,Dem,,,,HI,False,False
            ...
        """
        data = self.app.election.races
        self.app.log.info(
            'Getting races for election {0}'.format(
                self.app.election.electiondate
            )
        )
        if self.app.election._response:
            self.app.log.debug(
                'Elex API URL: {0}'.format(self.app.election._response.url)
            )
            self.app.log.debug(
                'ELAPI cache hit: {0}'.format(self.app.election._response.from_cache)
            )
            if self.app.election._response.from_cache:
                self.app.exit_code = 64

        self.app.render(data)

    @expose(help="Get reporting units")
    @require_ap_api_key
    @require_date_argument
    def reporting_units(self):
        """
        ``elex reporting-units <electiondate>``

        Returns reporting unit data for a given election date.

        Reporting units represent geographic aggregation of voting data at the
        national, state, county, and district level.

        Command:

        .. code:: bash

            elex reporting-units 2016-03-26

        Example output:

        .. csv-table::

            id,reportingunitid,reportingunitname,description,electiondate,fipscode,initialization_data,lastupdated,level,national,officeid,officename,precinctsreporting,precinctsreportingpct,precinctstotal,raceid,racetype,racetypeid,seatname,seatnum,statename,statepostal,test,uncontested,votecount
            state-1,state-1,,,2016-03-26,,False,2016-03-27T03:03:54Z,state,True,P,President,40,1.0,40,2919,Caucus,E,,,Alaska,AK,False,False,539
            county-2003,county-2003,State House District 1,,2016-03-26,,False,2016-03-27T03:03:54Z,county,True,P,President,1,1.0,1,2919,Caucus,E,,,,AK,False,False,12
            county-2004,county-2004,State House District 2,,2016-03-26,,False,2016-03-27T03:03:54Z,county,True,P,President,1,1.0,1,2919,Caucus,E,,,,AK,False,False,6
            ...
        """
        data = self.app.election.reporting_units
        self.app.log.info(
            'Getting reporting units for election {0}'.format(
                self.app.election.electiondate
            )
        )
        if self.app.election._response:
            self.app.log.debug(
                'Elex API URL: {0}'.format(self.app.election._response.url)
            )
            self.app.log.debug(
                'ELAPI cache hit: {0}'.format(self.app.election._response.from_cache)
            )
            if self.app.election._response.from_cache:
                self.app.exit_code = 64

        self.app.render(data)

    @expose(help="Get candidate reporting units (without results)")
    @require_ap_api_key
    @require_date_argument
    def candidate_reporting_units(self):
        """
        ``elex candidate-reporting-units <electiondate>``

        Returns candidate reporting unit data for a given election date.

        A candidate reporting unit is a container for the results of a voting
        in a specific reporting unit. This command is a close cousin of
        `elex results <electiondate>`.

        This command does not return results.

        Command:

        .. code:: bash

            elex candidate-reporting-units 2016-03-26

        Example output:

        .. csv-table::

            id,raceid,racetype,racetypeid,ballotorder,candidateid,description,delegatecount,electiondate,fipscode,first,incumbent,initialization_data,is_ballot_measure,last,lastupdated,level,national,officeid,officename,party,polid,polnum,precinctsreporting,precinctsreportingpct,precinctstotal,reportingunitid,reportingunitname,runoff,seatname,seatnum,statename,statepostal,test,uncontested,votecount,votepct,winner
            2919-polid-1445-None,2919,Caucus,E,2,6527,,0,2016-03-26,,Bernie,False,True,False,Sanders,2016-03-27T03:03:54Z,,True,P,President,Dem,1445,4262,0,0.0,0,,,False,,,Alaska,AK,False,False,0,0.0,False
            2919-polid-1746-None,2919,Caucus,E,1,6526,,0,2016-03-26,,Hillary,False,True,False,Clinton,2016-03-27T03:03:54Z,,True,P,President,Dem,1746,4261,0,0.0,0,,,False,,,Alaska,AK,False,False,0,0.0,False

        Notes:

        This command can be used to quickly create schemas.

        .. code:: bash

            pip install csvkit
            elex candidate-reporting-units 03-26-16 | csvsql -i mysql

        Will output:

        .. code:: sql

            CREATE TABLE stdin (
                id VARCHAR(23) NOT NULL,
                raceid INTEGER NOT NULL,
                racetype VARCHAR(6) NOT NULL,
                racetypeid VARCHAR(1) NOT NULL,
                ...
            );
        """
        data = self.app.election.candidate_reporting_units
        self.app.log.info(
            'Getting candidate reporting units for election {0}'.format(
                self.app.election.electiondate
            )
        )
        if self.app.election._response:
            self.app.log.debug(
                'Elex API URL: {0}'.format(self.app.election._response.url)
            )
            self.app.log.debug(
                'ELAPI cache hit: {0}'.format(self.app.election._response.from_cache)
            )
            if self.app.election._response.from_cache:
                self.app.exit_code = 64

        self.app.render(data)

    @expose(help="Get candidates")
    @require_ap_api_key
    @require_date_argument
    def candidates(self):
        """
        ``elex candidates <electiondate>``

        Returns candidate data for a given election date.

        Command:

        .. code:: bash

            elex candidates 2016-03-26

        Example output:

        .. csv-table::

            id,candidateid,ballotorder,first,last,party,polid,polnum
            polid-1445,6527,2,Bernie,Sanders,Dem,1445,4262
            polid-1746,6526,1,Hillary,Clinton,Dem,1746,4261
            ...
        """
        data = self.app.election.candidates
        self.app.log.info(
            'Getting candidates for election {0}'.format(
                self.app.election.electiondate
            )
        )
        if self.app.election._response:
            self.app.log.debug(
                'Elex API URL: {0}'.format(self.app.election._response.url)
            )
            self.app.log.debug(
                'ELAPI cache hit: {0}'.format(self.app.election._response.from_cache)
            )
            if self.app.election._response.from_cache:
                self.app.exit_code = 64

        self.app.render(data)

    @expose(help="Get ballot measures")
    @require_ap_api_key
    @require_date_argument
    def ballot_measures(self):
        """
        ``elex ballot-measures <electiondate>``

        Returns ballot measure data for a given election date.

        Command:

        .. code:: bash

            elex ballot-measures 2016-03-15

        Example output:

        .. csv-table::

            id,candidateid,ballotorder,description,electiondate,last,polid,polnum,seatname
            2016-03-15-43697,43697,1,,2016-03-15,For,,37229,Public Improvement Bonds
            2016-03-15-43698,43698,2,,2016-03-15,Against,,37230,Public Improvement Bonds
            ...
        """
        data = self.app.election.ballot_measures
        self.app.log.info(
            'Getting ballot measures for election {0}'.format(
                self.app.election.electiondate
            )
        )
        if self.app.election._response:
            self.app.log.debug(
                'Elex API URL: {0}'.format(self.app.election._response.url)
            )
            self.app.log.debug(
                'ELAPI cache hit: {0}'.format(self.app.election._response.from_cache)
            )
            if self.app.election._response.from_cache:
                self.app.exit_code = 64

        self.app.render(data)

    @expose(help="Get results")
    @require_ap_api_key
    @require_date_argument
    def results(self):
        """
        ``elex results <electiondate>``

        Returns result data.

        Each row in the output represents a fully flattened and
        denormalized version of a result for specific candidate in
        a specific race.

        Command:

        .. code:: bash

            elex results 2016-03-01

        Example output:

        .. csv-table::

            id,unique_id,raceid,racetype,racetypeid,ballotorder,candidateid,description,delegatecount,electiondate,fipscode,first,incumbent,initialization_data,is_ballot_measure,last,lastupdated,level,national,officeid,officename,party,polid,polnum,precinctsreporting,precinctsreportingpct,precinctstotal,reportingunitid,reportingunitname,runoff,seatname,seatnum,statename,statepostal,test,uncontested,votecount,votepct,winner
            3021-polid-61815-state-1,3021,Caucus,S,2,6528,,0,2016-03-01,,Ted,False,False,False,Cruz,2016-03-02T17:05:46Z,state,True,P,President,GOP,61815,4263,72,1.0,72,state-1,,False,,,Alaska,AK,False,False,7973,0.363566,True
            3021-polid-8639-state-1,3021,Caucus,S,5,6548,,0,2016-03-01,,Donald,False,False,False,Trump,2016-03-02T17:05:46Z,state,True,P,President,GOP,8639,4273,72,1.0,72,state-1,,False,,,Alaska,AK,False,False,7346,0.334975,False
            ...
        """
        data = self.app.election.results
        self.app.log.info('Getting results for election {0}'.format(
            self.app.election.electiondate
        ))
        if self.app.election._response:
            self.app.log.debug(
                'Elex API URL: {0}'.format(self.app.election._response.url)
            )
            self.app.log.debug(
                'ELAPI cache hit: {0}'.format(self.app.election._response.from_cache)
            )
            if self.app.election._response.from_cache:
                self.app.exit_code = 64

        self.app.render(data)

    @expose(help="Get list of available elections")
    @require_ap_api_key
    def elections(self):
        """
        ``elex elections``

        Returns all elections known to the API.

        Command:

        .. code:: bash

            elex elections

        Example output:

        .. csv-table::

            2016-02-09,2016-02-09,True,False
            2016-02-16,2016-02-16,True,False
            ...
        """
        self.app.log.info('Getting election list')
        elections = Elections().get_elections(
            datafile=self.app.pargs.data_file
        )
        self.app.render(elections)

    @expose(help="Get all delegate reports")
    @require_ap_api_key
    def delegates(self):
        """
        ``elex delegates``

        Returns delegate report data.

        Command:

        .. code:: bash

            elex delegates

        Example output:

        .. csv-table::

            level,party_total,superdelegates_count,last,state,candidateid,party_need,party,delegates_count,id,d1,d7,d30
            state,2472,0,Bush,MN,1239,1237,GOP,0,MN-1239,0,0,0
            state,2472,0,Bush,OR,1239,1237,GOP,0,OR-1239,0,0,0

        """
        self.app.log.info('Getting delegate reports')
        if (
            self.app.pargs.delegate_super_file and
            self.app.pargs.delegate_sum_file
        ):
            report = DelegateReport(
                delsuper_datafile=self.app.pargs.delegate_super_file,
                delsum_datafile=self.app.pargs.delegate_sum_file
            )
        else:
            report = DelegateReport()

        self.app.render(report.candidate_objects)

    @expose(help="Get the next election (if date is specified, will be \
relative to that date, otherwise will use today's date)")
    @require_ap_api_key
    def next_election(self):
        """
        ``elex next-election <date-after>``

        Returns data about the next election with an optional date
        to start searching.

        Command:

        .. code:: bash

            elex next-election

        Example output:

        .. csv-table::

            id,electiondate,liveresults,testresults
            2016-04-19,2016-04-19,False,True

        You can also specify the date to find the next election after, e.g.:

        .. code:: bash

            elex next-election 2016-04-15

        This will find the first election after April 15, 2016.
        """
        self.app.log.info('Getting next election')
        if len(self.app.pargs.date):
            electiondate = self.app.pargs.date[0]
        else:
            electiondate = None
        election = Elections().get_next_election(
            datafile=self.app.pargs.data_file,
            electiondate=electiondate
        )
        if election is None:
            self.app.log.error('No next election')
            self.app.close(1)

        self.app.render(election)

    @expose(help="Clear the elex response cache")
    def clear_cache(self):
        """
        ``elex clear-cache``

        Returns data about the next election with an optional date
        to start searching.

        Command:

        .. code:: bash

            elex clear-cache

        Example output:

        .. code:: bash

            2016-09-30 00:22:56,992 (INFO) cement:app:elex : Clearing cache (/var/folders/z2/plxshs7c43lm_bctxn/Y/elex-cache)
            2016-09-30 00:22:56,993 (INFO) cement:app:elex : Cache cleared.

        """
        from elex import cache
        adapter = cache.get_adapter('http://')
        self.app.log.info('Clearing cache ({0})'.format(adapter.cache.directory))
        try:
            rmtree(adapter.cache.directory)
        except OSError:
            self.app.log.info('No cache entries found.')
            self.app.close(64)
        else:
            self.app.log.info('Cache cleared.')


class ElexApp(CementApp):
    class Meta:
        label = 'elex'
        base_controller = ElexBaseController
        hooks = [
            ('post_setup', cachecontrol_logging_hook),
            ('post_argument_parsing', add_election_hook),
        ]
        extensions = [
            'elex.cli.ext_csv',
            'elex.cli.ext_json'
        ]
        output_handler = 'csv'

        handler_override_options = dict(
            output=(['-o'], dict(help='output format (default: csv)')),
        )
        log_handler = LoggingLogHandler(
            console_format=LOG_FORMAT,
            file_format=LOG_FORMAT
        )


def main():
    with ElexApp() as app:
        app.run()
