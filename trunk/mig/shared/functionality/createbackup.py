#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# --- BEGIN_HEADER ---
#
# createbackup - back end for backup archives
# Copyright (C) 2003-2017  The MiG Project lead by Brian Vinter
#
# This file is part of MiG.
#
# MiG is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# MiG is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
# -- END_HEADER ---
#

"""Creation of backup archives for write-once files"""

from shared.functionality.createfreeze import main as freeze_main, \
     signature as freeze_signature


def main(client_id, user_arguments_dict):
    """Main function used by front end"""

    # Mimic call to createfreeze with backup fields set
    args_dict = freeze_signature()[1]
    args_dict.update(user_arguments_dict)
    args_dict['flavor'] = ['backup']
    return freeze_main(client_id, args_dict)
