import youtube_dl
import os
import PySimpleGUI as sg

#some global vars because I am lazy
input = "input.txt"
output= "output"
config = "config"

#sys
cache_filename = 'cache'
ydl_opts = {'outtmpl':output + '/%(title)s.%(ext)s'}


def get_link_list(filename, clear=False, debug=False):
    links = list()
    file_check = os.path.isfile(filename)

    if not file_check:
        if debug:
            print("File '" + filename + "' not found!")
        return None
    with open(filename, "r") as file:
        if not file:
            if debug:
                print("File '" + filename + "' is empty!")
            return None
        for line in file:
            test_string = line.strip()
            if not test_string:
                continue
            links.append(line)
    if clear:
        os.remove(filename)

    return links


def update_cache(window, links):
    with open(cache_filename, "w") as file:
        for link in links:
            if not link.endswith('\n'):
                link += '\n'
            file.write(link)

    window.Element('OUTPUT').Update(values=links)


def write_setting(mode):
    with open(config, "w") as file:
        file.write(mode)

def get_new_links(window, values):
    links = list()
    if values and 'INPUT' in values:
        raw_data = values['INPUT']
        test_string = raw_data.strip()
        if test_string:
            links = raw_data.split()
            window.Element('INPUT').Update(value='')
            window.Element('OUTPUT').Update(values=links)
            return links

    return None

def download(window, values):
    cached_links = get_link_list(cache_filename, debug=True)
    new_links = get_new_links(window, values)
    links = list()
    if cached_links:
        links.extend(cached_links)
    if new_links:
        links.extend(new_links)

    if not links:
        window.Element('STATE').Update(value='State: Stopped. No Links!')
        return

    while links:

        event, values = window.read(timeout=0)
        if event.startswith('STOP'):
            update_cache(window, links)
            window.Element('STATE').Update(value='State: Stopped')
            return

        new_links = get_new_links(window, values)

        if new_links:
            links.extend(new_links)

        state_string = 'State: Downloading - Remaining: ' + str(len(links))
        window.Element('STATE').Update(value=state_string)

        link = links[0]
        link = link.rstrip("\n")
        if not link:
            links.pop(0)
            update_cache(window, links)
            continue

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            print("Downloading " + link)
            try:
                ydl.download([link])
            except:
                links.pop(0)
                update_cache(window, links)
                continue
            links.pop(0)
            update_cache(window, links)

    window.Element('STATE').Update(value='Done')


def set_mode(mode, window):
    global ydl_opts
    if mode == 'MP3':
        window.Element('CB1').Update(value=True)
        window.Element('CB2').Update(value=False)
        ydl_opts = {'format': 'bestaudio/best',
                    'extractaudio': True,
                    'audioformat': 'mp3',
                    'postprocessors': [{
                        'key': 'FFmpegExtractAudio',
                        'preferredcodec': 'mp3',
                        'preferredquality': '192',
                    }],
                    'outtmpl': output + '/%(title)s.%(ext)s'}
    elif mode == 'MP4':
        window.Element('CB1').Update(value=False)
        window.Element('CB2').Update(value=True)
        ydl_opts = {'format': 'best',
                    'outtmpl': output + '/%(title)s.%(ext)s'}

def main():
    """ Main entry point of the app """

    # ------ GUI Defintion ------ #
    layout = [
        [sg.Checkbox('MP3', default=True, enable_events=True, key='CB1'),
         sg.Checkbox('MP4', default=False, enable_events=True, key='CB2')],
        [sg.Multiline(size=(50, 20), key='INPUT') , sg.Listbox(size=(50, 20), key='OUTPUT', values=list())],
        [sg.Button('Start', enable_events=True, key='START'), sg.Button('Stop', enable_events=True, key='STOP')],
        [sg.Text('State: Init', size=(60, 1), key='STATE')]
    ]

    window = sg.Window("NeoMule",
                       layout,
                       default_element_size=(30, 1),
                       auto_size_text=True,
                       auto_size_buttons=True,
                       default_button_element_size=(30, 1),
                       finalize=True
                       )

    setting_mode = 'MP3'
    file_check = os.path.isfile(config)
    if file_check:
        with open(config, "r") as file:
            if not file:
                file.close()
            else:
                setting_mode = file.read()

    set_mode(setting_mode, window)

    window.Element('STATE').Update(value='State: Idle')

    while True:
        event, values = window.read()
        # End program if user closes window or
        # presses the OK button
        if event == sg.WIN_CLOSED:
            break

        if event.startswith('CB1'):
            setting_mode = 'MP3'
            set_mode(setting_mode, window)
            write_setting(setting_mode)
        if event.startswith('CB2'):
            setting_mode = 'MP4'
            set_mode(setting_mode, window)
            write_setting(setting_mode)

        if event.startswith('START'):
            window.Element('STATE').Update(value='State: Starting Download')
            download(window, values)


    window.close()


if __name__ == "__main__":
    """ This is executed when run from the command line """
    main()