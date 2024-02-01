#!/usr/bin/env python3
# Copyright 2023 Raffaele Mancuso
# SPDX-License-Identifier: GPL-2.0-or-later

import subprocess


def viewdf(df):
    head = """
    <html>

    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.7/css/jquery.dataTables.css" />
 
    <script src="https://code.jquery.com/jquery-3.7.1.slim.min.js"></script>

    <script src="https://cdn.datatables.net/1.13.7/js/jquery.dataTables.js"></script>

    <script>
        $(document).ready(function() {$('.dataframe').dataTable();});
    </script>

    <body>
    """
    foot = """
    </body>
    </html>
    """
    html = head + df.to_html() + foot
    with open("/tmp/table.html", "w") as fh:
        fh.write(html)
    subprocess.run(["xdg-open", "/tmp/table.html"])
