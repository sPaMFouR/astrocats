"""
"""
import re
import os

from . import producer, DIR_TEMPLATES
from .. import utils
from .. entry import ENTRY

_DISCLAIMER = ("All data collected by the OSC was originally generated by others, "
               "if you intend to use this data in a publication, we ask that you please cite "
               "the linked sources and/or contact the sources of the data directly.")

_ISSUE_TEXT = ("Please describe the issue with {EVENT_NAME}'s data here, be as descriptive "
               "as possible! If you believe the issue appears in other events as well, "
               "please identify which other events the issue possibly extends to.")

_FORCE_FRAME = \
    """
<script type="text/javascript">\n
        if(top==self)\n
        this.location="''' + event_name + '''"\n
</script>
    """

_NOTE_DERIVED = ("<p><em>Values that are colored <span class='derived'>purple</span> were "
                 "computed by the OSC using values provided by the specified sources.</em></p>")

_SOURCE_ENTRY = \
    """
<td class="event-cell" id="source{SRC_ALIAS}">{SRC_ALIAS}</td>
<td width=250px class="event-cell">
{SRC_LINES}
</td>
    """

_META_DATA_ENTRY = ("<tr><td class='event-cell'>{LABEL}</td>"
                    "<td width=250px class='event-cell'>{VALUE}</td></tr>\n")

_MARK_ERROR_BUTTON = ("<span class='sttt'><button class='sme' type='button' onclick='markError("
                      "'{EVENT_NAME}', '{KEY}', '{ID_TYPES_STR}', '{SOURCE_ID_STR}', "
                      "'{EDIT}', '{MODULE_NAME}')'>Flag as erroneous</button></span>")

_ADD_DATA_BUTTON = ("<span class='sttright'><button class='saq' "
                    "type='button' onclick='addQuantity('{EVENT_NAME}', '{KEY}', '{EDIT}', "
                    "'{MODULE_NAME}')'>Add new value</button></span>")

_PRIMARY_HEADER = ("<!--    PRIMARY    -->\n"
                   "<tr><th colspan='2' class='event-cell'>Primary Sources</th></tr>")
_SECONDARY_HEADER = ("<!--    SECONDARY    -->\n"
                     "<tr><th colspan='2' class='event-cell'>Secondary Sources</th></tr>")

_PRIVATE_SOURCE_LINE = "<span class='private-source'>Data from source not yet public</span>\n"


class HTML_Pro(producer.Producer_Base):

    SIMPLE_META_DATA_KEYS = [ENTRY.NAME]

    def __init__(self, catalog, args):
        log = catalog.log
        self.args = args
        self.catalog = catalog
        self.log = log
        log.debug("HTML_Pro.__init__()")

        # self.module_name = 'bh'
        self.module_name = catalog.module_name
        log.warning("`self.module_name` = '{}', is that right?".format(self.module_name))

        # Load specifications for columns to include in HTML pages from `catalog`
        self.COLUMNS = catalog.EVENT_HTML_COLUMNS

        self.HTML_OUT_DIR = catalog.PATHS.PATH_HTML

        event_page_fname = os.path.join(DIR_TEMPLATES, 'event_page.html')
        self.EVENT_PAGE = self._load_content_from(event_page_fname)
        sources_table_fname = os.path.join(DIR_TEMPLATES, 'sources_table.html')
        self.SOURCES_TABLE = self._load_content_from(sources_table_fname)
        meta_data_table_fname = os.path.join(DIR_TEMPLATES, 'meta_data_table.html')
        self.META_DATA_TABLE = self._load_content_from(meta_data_table_fname)

        if args.test:
            self.FORCE_FRAME = ""
        else:
            self.FORCE_FRAME = _FORCE_FRAME

        return

    def _generate_meta_data_table(self, event_name, event_data):

        # Check if this corresponds to an 'internal' file
        edit = str(self.catalog.PATHS.is_internal_event(event_name)).lower()

        meta_data = []
        derived_flag = False
        for key, col_vals in self.COLUMNS.items():
            header = col_vals[0]
            if (key not in event_data) or (len(event_data[key]) == 0):
                continue

            value_html = []
            if isinstance(event_data[key], str):
                subentry = re.sub('<[^<]+?>', '', event_data[key])
                value_html.append(subentry)
            else:
                for r, row in enumerate(event_data[key]):
                    if ('value' in row) and ('source' in row):
                        # Create list of source-aliases for value superscript
                        # ---------------------------------------------------
                        _srcs = [x.strip() for x in row['source'].split(',')]
                        _srcs = sorted(_srcs, key=lambda x:
                                       float(x) if utils.is_number(x) else float("inf"))
                        sourcehtml = ["<a href='#source{src}' target='_self'>{src}</a>".format(
                            src=str(x)) for x in _srcs]
                        sourcehtml = ", ".join(sourcehtml)
                        sup_sources = "<sup>{SOURCEHTML}</sup>".format(SOURCEHTML=sourcehtml)

                        # Create the printed value
                        # ------------------------
                        val = row['value']
                        if 'e_value' in row:
                            val += r' ± ' + row['e_value']

                        if 'derived' in row and row['derived']:
                            derived_flag = True
                            _value_html = "<span class='derived'>{}</span>".format(val)
                        else:
                            _value_html = "{}".format(val)

                        # Create Mark erroneous button
                        # ----------------------------
                        sourceids = []
                        idtypes = []
                        for alias in row['source'].split(','):
                            for source in event_data['sources']:
                                if source['alias'] == alias:
                                    if 'bibcode' in source:
                                        sourceids.append(source['bibcode'])
                                        idtypes.append('bibcode')
                                    elif 'arxivid' in source:
                                        sourceids.append(source['arxivid'])
                                        idtypes.append('arxivid')
                                    else:
                                        sourceids.append(source['name'])
                                        idtypes.append('name')
                        if (not sourceids) or (not idtypes):
                            raise ValueError("Unable to find associated source by alias!")

                        id_types_str = ','.join(idtypes)
                        source_id_str = ','.join(sourceids)
                        mark_error_button = _MARK_ERROR_BUTTON.format(
                            EVENT_NAME=event_name, KEY=key, ID_TYPES_STR=id_types_str,
                            SOURCE_ID_STR=source_id_str, EDIT=edit, MODULE_NAME=self.module_name)

                        # Combine into value cell
                        # -----------------------
                        value_html.append("<div class='stt'>" + _value_html + mark_error_button +
                                          "</div>" + sup_sources)

                    elif isinstance(row, str):
                        value_html.append(row.strip())

            if len(value_html):
                if key not in self.SIMPLE_META_DATA_KEYS:
                    button = _ADD_DATA_BUTTON.format(
                        HEADER=header, EVENT_NAME=event_name, KEY=key, EDIT=edit,
                        MODULE_NAME=self.module_name)
                    label_html = "<div class='stt'>{HEADER}{BUTTON}</div>".format(
                        HEADER=header, BUTTON=button)
                else:
                    label_html = header

                value_html = "<br>".join(value_html)
                md_line = "<!--    {}    -->\n".format(key.upper())
                md_line += _META_DATA_ENTRY.format(LABEL=label_html, VALUE=value_html)
                meta_data.append(md_line)

        meta_data_lines = "\n".join(meta_data)
        if derived_flag:
            derived = _NOTE_DERIVED
        else:
            derived = ""
        meta_data_table = self.META_DATA_TABLE.format(
            META_DATA_LINES=meta_data_lines, DERIVED=derived)

        return meta_data_table

    def _generate_sources_table(self, event_data):
        srcs = ''
        if ('sources' not in event_data) or (len(event_data['sources']) == 0):
            return srcs

        prims = []
        secs = []
        for source in event_data['sources']:
            src, secondary_flag = self._source_entry(source)
            if secondary_flag:
                secs.append(src)
            else:
                prims.append(src)

        primary_sources = ''
        if len(prims):
            primary_sources += _PRIMARY_HEADER
            primary_sources += "\n".join("<tr>\n{}\n</tr>".format(ps) for ps in prims)

        secondary_sources = ''
        if len(secs):
            secondary_sources += _SECONDARY_HEADER
            secondary_sources += "\n".join("<tr>\n{}\n</tr>".format(ss) for ss in secs)

        sources_table = self.SOURCES_TABLE.format(PRIMARY_SOURCES=primary_sources,
                                                  SECONDARY_SOURCES=secondary_sources)

        return sources_table

    def _source_entry(self, source):
        """Go through an individual 'source' and generate the sources-table entry for it.

        Places content into a filled version of `_SOURCE_ENTRY`.
        """

        biburl = ''
        if 'bibcode' in source:
            biburl = 'http://adsabs.harvard.edu/abs/' + source['bibcode']

        refurl = source.get('url', '')
        name = source.get('name')
        bibcode = source.get('bibcode')
        arxiv = source.get('arxivid')
        if name is not None:
            source_name = name
        elif bibcode is not None:
            source_name = bibcode
        else:
            source_name = arxiv
        # Determine if this is a secondary source
        secondary_flag = source.get('secondary', False)

        source_lines = []
        # Add name line (with hyperlink if possible)
        if (bibcode is None) or (source_name != bibcode):
            _code_name = source_name.encode('ascii', 'xmlcharrefreplace').decode("utf-8")
            if refurl:
                _url = "<a href='{}'>{}</a>".format(refurl, _code_name)
            else:
                _url = _code_name
            source_lines.append(_url)

        if 'reference' in source:
            source_lines.append(source['reference'])

        if bibcode is not None:
            if 'reference' in source:
                _val = "<a href='{}'>{}</a>".format(biburl, bibcode)
            else:
                _val = bibcode
            _val = "[" + _val + "]"
            source_lines.append(_val)

        if source.get('private', False):
            source_lines.append(_PRIVATE_SOURCE_LINE)

        src_lines = "<br>".join(source_lines)
        src = _SOURCE_ENTRY.format(SRC_ALIAS=source['alias'], SRC_LINES=src_lines)
        return src, secondary_flag

    def _load_content_from(self, fname):
        with open(fname, 'r') as cont_file:
            content = cont_file.read()
        return content

    def produce(self, fname, event_name, event_data):
        self.log.debug("HTML_Pro.produce()")

        # Prepare quantities
        # ------------------
        download_path = "\"../json/{event_name}.json\"".format(event_name=event_name)
        github_url = "https://github.com/astrocatalogs/blackholes"
        issue_text = _ISSUE_TEXT.format(EVENT_NAME=event_name)

        # Generate the table for meta-data
        meta_data_table = self._generate_meta_data_table(event_name, event_data)
        # Generate the table for sources
        sources_table = self._generate_sources_table(event_data)

        # Fill in the page values
        # -----------------------
        event_page = self.EVENT_PAGE.format(
            DOWNLOAD_PATH=download_path, EVENT_NAME=event_name, GITHUB_URL=github_url,
            DISCLAIMER=_DISCLAIMER, ISSUE_TEXT=issue_text, FORCE_FRAME=self.FORCE_FRAME,
            SOURCES_TABLE=sources_table, META_DATA_TABLE=meta_data_table)

        # Save to file(s)
        # ---------------
        fname_out = os.path.join(self.HTML_OUT_DIR, event_name + ".html")
        if self.args.test:
            self._save(fname_out, event_page)
        else:
            self.touch(fname_out)
        self._save_gzip(fname_out, event_page.encode(), lvl=self.log.INFO)

        return