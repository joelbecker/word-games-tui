import asyncio
import curses
from datetime import datetime, timedelta
from utils import vertical_buffer, horizontal_buffer, display_rows, display_cols
from concurrent.futures import ThreadPoolExecutor

async def loading_animation(stdscr, fetch_fn, message, min_time=1):
    """
    Display a loading animation while waiting for fetch_fn to complete.
    
    Args:
        stdscr: Curses window object
        fetch_fn: Function that performs the data fetching
        message: Message to display during loading
    
    Returns:
        The result from fetch_fn
    """
    stdscr.nodelay(True)
    animation = ["|", "/", "-", "\\"]
    idx = 0
    stdscr.clear()
    start_time = datetime.now()

    with ThreadPoolExecutor() as executor:
        try:
            future = executor.submit(fetch_fn)
            # Wait for both minimum time AND future completion
            while future.running() or (datetime.now() - start_time) < timedelta(seconds=min_time):
                vbuffer = vertical_buffer(1, display_rows(stdscr))
                hbuffer = horizontal_buffer(len(message) + 1, display_cols(stdscr))
                stdscr.addstr(vbuffer, hbuffer, message + animation[idx % len(animation)])
                stdscr.refresh()
                
                idx += 1
                await asyncio.sleep(0.1)
                
                try:
                    key = stdscr.getch()
                    if key == ord('q'):
                        return None
                except curses.error:
                    pass
        
            return future.result()
        
        except Exception as e:
            stdscr.endwin()
            print("An error occurred while loading the puzzle.")
            if input("Would you like to enter debug mode? (y/n): ").lower() == "y":
                print(f"Exception: {e}")
                import pdb; pdb.set_trace()
                exit()
            else:
                raise e

# Helper function to run the animation in the event loop
def run_loading_animation(stdscr, fetch_fn, message, min_time=1):
    """
    Wrapper function to run the loading animation in the event loop.
    """
    return asyncio.run(loading_animation(stdscr, fetch_fn, message, min_time))
