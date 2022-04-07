# -*- coding: utf-8 -*-

"""
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

__author__ = 'Basil Eric Rabi'
__date__ = '2022-04-07'
__copyright__ = '(C) 2022 by Basil Eric Rabi'
__revision__ = '$Format:%H$'


try:
    import ezdxf # pyright: reportMissingImports=false
except ImportError:
    import os
    import platform
    import sys
    from pathlib import Path
    this_dir = os.path.dirname(os.path.realpath(__file__))
    plugin_dir = Path(this_dir).parent
    path = os.path.join(plugin_dir, 'lib', 'pyparsing-3.0.7-py3-none-any.whl')
    sys.path.append(path)
    path = os.path.join(plugin_dir, 'lib', 'typing_extensions-4.1.1-py3-none-any.whl')
    sys.path.append(path)
    if platform.system() == 'Windows':
        if platform.machine() == 'AMD64':
            path = os.path.join(plugin_dir, 'lib', 'ezdxf-0.17.2-cp310-cp310-win_amd64.whl')
            sys.path.append(path)
            import ezdxf
        else:
            raise Exception('System not yet supported. Contact plugin author.')
    else:
        raise Exception('Module not found. Install ezdxf: `pip install ezdxf`.')

new_dxf = ezdxf.new
