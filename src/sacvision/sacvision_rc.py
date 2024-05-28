'''
Created on May 14, 2024

@author: luis
'''

from pathlib import Path
import inspect

from PySide6.QtCore import QResource

        
def init_resource():
    local_dir = Path(inspect.getabsfile(init_resource)).parent.resolve()
    rcc_name = str(local_dir / 'data/sacvision.rcc')
    QResource.registerResource(rcc_name)
        
init_resource()