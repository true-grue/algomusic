# algomusic

https://youtu.be/WNs8t5Yjm7o

```
from traitlets.config.manager import BaseJSONConfigManager
from pathlib import Path
path = Path.home() / ".jupyter" / "nbconfig"
cm = BaseJSONConfigManager(config_dir=str(path))
cm.update(
    "rise",
    {
        "theme": "white",
        "transition": "none",
        "start_slideshow_at": "selected",
     }
)
```

[part1](https://nbviewer.jupyter.org/github/true-grue/algomusic/blob/master/algomusic_part1.ipynb)

[part2](https://nbviewer.jupyter.org/github/true-grue/algomusic/blob/master/algomusic_part2.ipynb)
