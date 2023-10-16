# license is gnu agpl 3 - gnu.org/licenses/agpl-3.0.en.html

import asyncio
import sys
from main import main

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(' exiting ')
        sys.exit()

