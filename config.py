import os
# import socket
import subprocess
# import sys
import requests
import geocoder
import psutil
from libqtile import bar, hook, layout, qtile, widget
from libqtile.utils import send_notification
from libqtile.config import (
    DropDown,
    EzClick,
    EzDrag,
    EzKey,
    Group,
    Match,
    ScratchPad,
    Screen,
    KeyChord,
    Key,
)
from libqtile.lazy import lazy

def get_monitors():
    xr = subprocess.check_output('xrandr --query | grep " connected"', shell=True).decode().split('\n')
    monitors = len(xr) - 1 if len(xr) > 2 else len(xr)
    # if subprocess.check_output('xrandr --query', text)
    # try:
    #     monitors = (subprocess.check_output('xrandr --query | grep " connected" | grep -Eo "[0-9]{3,4}x[0-9]{3,4}"', shell=True).decode().split()
    return monitors

monitors = get_monitors()

home = os.environ["HOME"]
terminal = os.environ["TERMINAL"]
browser = os.environ["BROWSER"]
editor = terminal + " -e " + os.environ["EDITOR"]
reader = os.environ["READER"]
file_manager = terminal + " -e ranger"
email = terminal + " -e neomutt"
calender = terminal + " -e calcurse"
rss = terminal + " -e newsboat"

colors = [
    ["#282a36", "#282a36"],
    ["#ff5555", "#ff5555"],
    ["#50fa7b", "#50fa7b"],
    ["#f1fabc", "#f1fa8c"],
    ["#bd93f9", "#bd93f9"],
    ["#ff79c6", "#ff79c6"],
    ["#8be9fd", "#8be9fd"],
    ["#bfbfbf", "#bfbfbf"],
    ["#f8f8f2", "#f8f8f2"],
]

font = "Mononoki Nerd Font"
fontsize = 11

def get_todos():
    mail_todos = int(
        subprocess.check_output(
            "find {}/.local/share/mail/*/[Tt][Oo][Dd][Oo]/[cn][ue][rw] -type f"
            " | wc -l".format(home),
            shell=True,
        )
        .decode()
        .strip("\n")
    )
    calender_todos = int(
        subprocess.check_output("calcurse -t | tail -n +2 | wc -l", shell=True)
        .decode()
        .strip("\n")
    )
    return "  " + str(mail_todos + calender_todos)


def get_appointments():
    appointments = (
        subprocess.check_output(
            r"calcurse -d1 | tail -n +2 | grep '\*\|-' | wc -l", shell=True
        )
        .decode()
        .strip("\n")
    )
    return "  " + appointments


def get_news():
    news = (
        subprocess.check_output(
            "find {}/.config/emacs/.local/elfeed/db/data/*/* -type f | wc -l".format(
                home
            ),
            shell=True,
        ).decode().strip()
        )
        # subprocess.check_output(
        #     "newsboat -x print-unread | awk '{print $1}'", shell=True
        # )
        # .decode()
        # .strip("\n")
    # )
    # if news == "Error:":
        # news = "N/A"
    return "  " + news


def fuuny_bar(qtile):
    bar = getattr(qtile.current_screen, "bottom")
    if bar.is_show():
        qtile.widgets_map["widgetbox"].cmd_toggle()
        bar.show(False)
    else:
        # bar.size = 35
        # bar.finalize()
        bar.show()
        qtile.widgets_map["widgetbox"].cmd_toggle()


def get_mail():
    mail = (
        subprocess.check_output(
            "find {}/mail/*/[Ii][Nn][Bb][Oo][Xx]/new/* -type f | wc -l".format(
                home
            ),
            shell=True,
        )
        .decode()
        .strip("\n")
    )
    return "  " + mail


def get_covid():
    r = requests.get("https://api.corona-zahlen.org/germany")
    d = r.json()
    a = "Covid-19: " + str(d["delta"]["cases"])
    +" [" + str(round(d["weekIncidence"])) + "]"
    return a


def get_weather():
    location = geocoder.ip("me").city
    r = requests.get("http://wttr.in/{}?format=Weather:+%C+%t".format(location))
    return r.text


def get_df():
    partitions = ["/", "/home", "/media"]
    a = "Disk:"
    for p in partitions:
        a += (
            " "
            + subprocess.check_output(
                "df -h "
                + p
                + " | tail -n 1 | awk -F' ' '{print $6 \" \" $3 \"/\" $2}'",
                shell=True,
            )
            .decode()
            .strip()
        )
    return a


def get_backlight():
    return (
        " "
        + subprocess.check_output("xbacklight -get", shell=True).decode().strip()
        + "%"
    )


def up_backlight(qtile):
    subprocess.check_output(
        "xbacklight -inc 5 && xbacklight -get > /tmp/xobpipe", shell=True
    )
    qtile.widgets_map["backlight"].tick()


def down_backlight(qtile):
    subprocess.check_output(
        "xbacklight -dec 5 && xbacklight -get > /tmp/xobpipe", shell=True
    )
    qtile.widgets_map["backlight"].tick()


def get_volume():
    vol = subprocess.getoutput("pamixer --get-volume-human")
    if vol == "muted":
        return " "
    elif int(vol.strip('%')) < 30:
        return " " + vol
    elif int(vol.strip('%')) < 70:
        return " " + vol
    else:
        return " " + vol


def up_volume(qtile):
    subprocess.check_output(
        "pamixer -i 5 && pamixer --get-volume > /tmp/xobpipe", shell=True
    )
    qtile.widgets_map["volume"].tick()


def down_volume(qtile):
    subprocess.check_output(
        "pamixer -d 5 && pamixer --get-volume > /tmp/xobpipe", shell=True
    )
    qtile.widgets_map["volume"].tick()


def toggle_mute(qtile):
    if subprocess.getoutput("pamixer --get-mute") == "true":
        subprocess.check_output(
            "pamixer -t && pamixer --get-volume > /tmp/xobpipe", shell=True
        )
    else:
        subprocess.check_output("pamixer -t && echo 0 > /tmp/xobpipe", shell=True)
    qtile.widgets_map["volume"].tick()


def get_memory():
    mem = psutil.virtual_memory()
    if mem.used >= 1000 * 1024 * 1024:
        used = str(round(mem.used / (1024 ** 3), 2)) + "G"
    else:
        used = str(round(mem.used / (1024 ** 2))) + "M"
    total = str(round(mem.total / (1024 ** 3), 2)) + "G"
    return "Memory: " + used + "/" + total


def get_cpu():
    freq = round(psutil.cpu_freq().current / 1000, 1)
    percent = psutil.cpu_percent(interval=1)
    return "CPU: " + str(freq) + "GHz [" + str(percent) + "%]"

mail = widget.GenPollText(
    foreground=colors[1],
    func=get_mail,
    name="mail",
    update_interval=120,
    mouse_callbacks={"Button1": lambda: qtile.cmd_spawn(email)},
)

news = widget.GenPollText(
    foreground=colors[3],
    func=get_news,
    name="news",
    update_interval=120,
    mouse_callbacks={"Button1": lambda: qtile.cmd_spawn(rss)},
)

appointments = widget.GenPollText(
    foreground=colors[4],
    name="appointments",
    func=get_appointments,
    update_interval=1800,
    mouse_callbacks={"Button1": lambda: qtile.cmd_spawn(terminal + " -e calcurse")},
)

todos = widget.GenPollText(
    foreground=colors[5],
    name="todos",
    func=get_todos,
    update_interval=1800,
    mouse_callbacks={
        "Button1": lambda: qtile.cmd_spawn(terminal + ' -e neomutt -f "=TODO"'),
        "Button2": lambda: qtile.cmd_spawn(terminal + " -e calcurse"),
    },
)

xbacklight = widget.GenPollText(
    foreground=colors[1],
    name="backlight",
    func=get_backlight)

volume = widget.GenPollText(
    foreground=colors[2],
    name="volume",
    func=get_volume)

df = widget.GenPollText(name="df", func=get_df)

memory = widget.GenPollText(name="memory", func=get_memory, update_interval=5)

cpu = widget.GenPollText(name="cpu", func=get_cpu, update_interval=5)

music = widget.Mpd2(
    status_format="| Music: {play_status} {artist} - {title}",
    play_states={"stop": "", "play": "", "pause": ""},
    idle_format="",
)

updates = widget.CheckUpdates(
    distro="Arch",
    colour_have_updates=colors[2],
    colour_no_updates=colors[2],
    display_format="  {updates}",
    no_update_string="  0",
    custom_command='pacman -Qu | grep -Fv "[ignored]"',
    update_interval=3600,
    mouse_callbacks={"Button1": lambda: qtile.cmd_spawn(terminal + " -e yay -Syu"),
                     "Button2": lambda: send_notification("Hello", "message")},
)

sep = widget.Sep(
    size_percent=50,
    padding=8,
    linewidth=0)

# vol_text = widget.TextBox("Volume: ")

# vol = widget.PulseVolume(
#         volume_down_command='pamixer -d 3',
#         volume_up_command='pamixer -i 3',
#         mouse_callbacks={
#             'Button1': lambda: qtile.cmd_spawn("pavucontrol")
#             }
#         )

battery = widget.Battery(
    foreground=colors[3],
    format="Battery: {percent:2.0%} {char}",
    discharge_char="",
    full_char="",
    charge_char=" ",
    show_short_text=False,
    mouse_callbacks={
        "Button1": lambda: subprocess.check_output(
            'notify-send "$(/usr/bin/acpi)"', shell=True
        )
    },
)

clock = widget.Clock(
    foreground=colors[4],
    format="  %Y-%m-%d %a %I:%M %p",
    mouse_callbacks={"Button1": lambda: qtile.cmd_spawn(terminal + "-e nmtui")},
)

systray = widget.Systray()


temp_text = widget.TextBox("Temperature:")

temp = widget.ThermalSensor(foreground=colors[8])

covid = widget.GenPollText(
    func=get_covid,
    name="covid",
    update_interval=3600,
    mouse_callbacks={
        "Button1": lambda: qtile.cmd_spawn(
            browser + " https://www.rki.de/DE/Content/InfAZ/N/"
            "Neuartiges_Coronavirus/Fallzahlen.html"
        )
    },
)


weather = widget.GenPollText(
    func=get_weather,
    name="weather",
    update_interval=3600,
    mouse_callbacks={
        "Button1": lambda: qtile.cmd_spawn(browser + " http://wttr.in/Cologne")
    },
)


net = widget.Net(format="Traffic:{down} ↓↑ {up}")


wlan = widget.Wlan(interface="wlp3s0", format="Network: {essid} [{percent:2.0%}]")

""" LAYOUT THEME """
layout_theme = {
    "border_width": 3,
    "margin": 5,
    "border_focus": colors[4][0],
    "border_normal": colors[0][0],
}

mod = "mod4"

keys = [
    EzKey("M-q", lazy.window.kill(), desc="Close/kill window"),
    KeyChord(
        [mod],
        "space",
        [
            KeyChord(
                [],
                "w",
                [
                    EzKey("l", lazy.layout.increase_ratio()),
                    EzKey("h", lazy.layout.decrease_ratio()),
                    EzKey("k", lazy.layout.increase_nmaster()),
                    EzKey("j", lazy.layout.decrease_nmaster()),
                ],
                mode=(
                    "Windows: l -> increase ratio, "
                    "h -> decrease ratio "
                    "k -> increase # master "
                    "j -> decrease # master"
                ),
            )
        ],
        mode="KeyChord mode",
    ),
    KeyChord(
        [mod],
        "z",
        [  # Start chord by pressing Mod+z
            KeyChord(
                [],
                "x",
                [  # Continue chord with "x"
                    Key(
                        [],
                        "c",
                        lazy.spawn(terminal),
                    ),
                    Key(
                        [],
                        "b",
                        lazy.spawn(email),
                    ),
                ],
                mode="bb",
            )
        ],
        mode="vim",
    ),
    KeyChord(
        [mod],
        "m",
        [
            EzKey("m", lazy.spawn(terminal + " -e ncmpcpp")),
            KeyChord(
                [],
                "y",
                [
                    EzKey("p", lazy.spawn("ytfzf -mD")),
                    EzKey("d", lazy.spawn("ytfzf -mdD")),
                ],
                mode="p: play, d: download",
            ),
            EzKey("d", lazy.spawn("mpdmenu")),
            EzKey("p", lazy.spawn("mpdmenu -p")),
            EzKey("t", lazy.spawn("mpc toggle")),
            EzKey("l", lazy.spawn("mpc next")),
            EzKey("h", lazy.spawn("mpc prev")),
        ],
        mode="m: player, y: youtube, d(p): mpdmenu, t: play/pause, l: next, h: prev",
    ),
    # KeyChord([mod], "y", [
    #     EzKey(
    # Switch between windows
    EzKey("M-h", lazy.layout.left(), desc="Move focus left"),
    EzKey("M-l", lazy.layout.right(), desc="Move focus right"),
    EzKey("M-j", lazy.layout.down(), desc="Move focus down"),
    EzKey("M-k", lazy.layout.up(), desc="Move focus up"),
    # EzKey(
    #     "M-<space>", lazy.group.next_window(), desc="Move window focus to other window"
    # ),
    EzKey("M-b", lazy.function(fuuny_bar)),
    # EzKey("M-b", lazy.hide_show_bar(position="bottom")),
    EzKey("M-S-b", lazy.hide_show_bar(position="top")),
    EzKey("M-C-b", lazy.hide_show_bar()),
    EzKey("M-f", lazy.window.toggle_fullscreen()),
    EzKey("M-S-f", lazy.layout.maximize()),
    # Move windows between left/right columns or move up/down in current stack.
    # Moving out of range in Columns layout will create new column.
    EzKey("M-S-h", lazy.layout.shuffle_left(), desc="Move window to the left"),
    EzKey("M-S-l", lazy.layout.shuffle_right(), desc="Move window to the right"),
    EzKey("M-S-j", lazy.layout.shuffle_down(), desc="Move window down"),
    EzKey("M-S-k", lazy.layout.shuffle_up(), desc="Move window up"),
    EzKey("M-A-k", lazy.layout.increase_nmaster()),
    EzKey("M-A-j", lazy.layout.decrease_nmaster()),
    EzKey("M-A-l", lazy.layout.increase_ratio()),
    EzKey("M-A-h", lazy.layout.decrease_ratio()),
    # Grow windows. If current window is on the edge of screen and direction
    # will be to screen edge - window would shrink.
    EzKey("M-C-h", lazy.layout.grow_left(), desc="Grow window to the left"),
    EzKey("M-C-l", lazy.layout.grow_right(), desc="Grow window to the right"),
    EzKey("M-C-j", lazy.layout.grow_down(), desc="Grow window down"),
    EzKey("M-C-k", lazy.layout.grow_up(), desc="Grow window up"),
    EzKey("M-C-n", lazy.layout.normalize(), desc="Reset all window sizes"),
    # Screens
    EzKey("M-<period>", lazy.next_screen(), desc="Move focus to nect screen"),
    # Key([mod], "period", lazy.next_screen(), desc="Move focus to nect screen"),
    # Toggle between split and unsplit sides of stack.
    # Split = all windows displayed
    # Unsplit = 1 window displayed, like Max layout, but still with
    # multiple stack panes
    EzKey(
        "M-C-<Return>",
        lazy.layout.toggle_split(),
        desc="Toggle between split and unsplit sides of stack",
    ),
    EzKey("M-<Return>", lazy.spawn(terminal), desc="Launch terminal"),
    # Toggle between different layouts as defined below
    EzKey("M-S-<Tab>", lazy.next_layout(), desc="Toggle between layouts"),
    EzKey("M-C-r", lazy.restart(), desc="Restart Qtile"),
    EzKey("M-C-q", lazy.shutdown(), desc="Shutdown Qtile"),
    # Apps
    EzKey("M-d", lazy.spawn("mydock")),
    EzKey("M-p", lazy.spawn("dmenu_run -c -l 20")),
    EzKey("M-w", lazy.spawn(browser)),
    EzKey("M-S-w", lazy.spawn("dmenu_websearch")),
    EzKey("M-C-w", lazy.spawn(browser + " ~/dox/wiki/html/index.html")),
    EzKey("M-e", lazy.spawn(email)),
    # EzKey(
    #     "M-S-e",
    #     lazy.spawn(
    #         terminal
    #         + " -e abook -C ~/.config/abook/abookrc --datafile .local/share/abook/addressbook"
    #     ),
    # ),
    EzKey("M-S-e", lazy.spawn("emacsclient -c -a emacs")),
    # EzKey("M-m", lazy.spawn(terminal + ' -e ncmpcpp')),
    EzKey("M-S-m", lazy.spawn("mpdmenu")),
    EzKey("M-A-m", lazy.spawn("mpdmenu -p")),
    EzKey("M-C-m", lazy.spawn("ytfzf -mD")),
    EzKey("M-n", lazy.spawn(terminal + " -e nvim -c VimwikiIndex")),
    EzKey("M-S-n", lazy.spawn(rss)),
    EzKey("M-r", lazy.spawn(file_manager)),
    EzKey("M-S-r", lazy.spawn(terminal + " -e htop")),
    EzKey("M-c", lazy.spawn(terminal + " -e calcurse")),
    EzKey("M-<BackSpace>", lazy.spawn("sysact")),
    EzKey("M-y", lazy.spawn(terminal + " -e ytfzf -t")),
    EzKey("M-S-y", lazy.spawn("ytfzf -D")),
    # Clipboard
    EzKey(
        "<Insert>",
        lazy.function(
            lambda qtile: subprocess.Popen(
                ['notify-send "Clipboard contents:" "$(xclip -o selection clipboard)"'],
                shell=True,
            )
        ),
    ),
    # Volume
    EzKey("<XF86AudioRaiseVolume>", lazy.function(up_volume)),
    EzKey("M-<Up>", lazy.function(up_volume)),
    EzKey("<XF86AudioLowerVolume>", lazy.function(down_volume)),
    EzKey("M-<Down>", lazy.function(down_volume)),
    EzKey("<XF86AudioMute>", lazy.function(toggle_mute)),
    EzKey(
        "<XF86AudioMicMute>",
        lazy.spawn("pactl set-source-mute @DEFAULT_SOURCE@ toggle"),
    ),
    EzKey("<XF86AudioPrev>", lazy.spawn("mpc prev")),
    EzKey("M-<Left>", lazy.spawn("mpc prev")),
    EzKey("M-S-p", lazy.spawn("mpc toggle")),
    EzKey("<XF86AudioNext>", lazy.spawn("mpc next")),
    EzKey("M-<Right>", lazy.spawn("mpc next")),
    EzKey("<XF86AudioPause>", lazy.spawn("mpc next")),
    # Backlight
    EzKey("M-S-<Up>", lazy.function(up_backlight)),
    EzKey("M-S-<Down>", lazy.function(down_backlight)),
    # F-keys
    EzKey(
        "M-<F1>",
        lazy.function(
            lambda qtile: subprocess.Popen(
                [
                    "gen-keybinding-img -o .config/qtile/keybindings && ls ~/.config/qtile/keybindings | sxiv -N keybindings -g 1260x800 -z 100 -aio 2>/dev/null"
                ],
                shell=True,
            )
        ),
    ),
    EzKey(
        "M-<F2>",
        lazy.function(
            lambda qtile: subprocess.Popen(
                [
                    'man -k . | dmenu -l 30 | awk "{print $1}" | xargs -r man -Tpdf | zathura -'
                ],
                shell=True,
            )
        ),
    ),
    EzKey("M-<F3>", lazy.spawn("displayselect")),
    EzKey("M-<F4>", lazy.spawn(terminal + " -e pulsemixer")),
    EzKey(
        "M-<F11>",
        lazy.function(
            lambda qtile: subprocess.Popen(
                [
                    "mpv --no-cache --no-osc --no-input-default-bindings --input-conf=/dev/null --title=webcam $(ls /dev/video[0,2,4,6,8] | tail -n 1)"
                ],
                shell=True,
            )
        ),
    ),
    EzKey("M-S-<Return>", lazy.group["scratchpad"].dropdown_toggle("term")),
    EzKey("M-A-<Return>", lazy.group["scratchpad"].dropdown_toggle("qterm")),
]

scratchpad = [
    ScratchPad(
        "scratchpad",
        [
            DropDown("term", terminal, height=0.6, width=0.6, x=0.2, y=0.2),
            DropDown(
                "qterm",
                terminal + " -e qtile shell",
                height=0.6,
                width=0.6,
                x=0.2,
                y=0.2,
            ),
        ],
    )
]

norm_groups = [Group(i) for i in "123456789"]
groups = scratchpad + norm_groups

for i in groups[1:]:
    keys.extend(
        [
            EzKey(
                "M-%s" % i.name,
                lazy.group[i.name].toscreen(),
                desc="Switch to group {}".format(i.name),
            ),
            EzKey(
                "M-S-%s" % i.name,
                lazy.window.togroup(i.name, switch_group=True),
                desc="Switch to & move focused window to group {}".format(i.name),
            ),
            EzKey(
                "M-C-%s" % i.name,
                lazy.window.togroup(i.name, switch_group=False),
                desc="Move focused window to group {}".format(i.name),
            ),
        ]
    )

for i in range(monitors):
    keys.extend([EzKey("M-A-%s" % i, lazy.window.toscreen(i))])

layouts = [
    layout.MonadTall(single_margin=0, single_border_width=0, **layout_theme),
    layout.MonadWide(single_margin=0, single_border_width=0, **layout_theme),
    layout.Tile(
        ratio=0.5,
        add_on_top=False,
        add_after_last=True,
        shift_windows=True,
        **layout_theme
    ),
    layout.Bsp(**layout_theme),
    layout.Max(),
    layout.Stack(num_stacks=2),
]

widget_defaults = dict(
    font=font, fontsize=fontsize, padding=2, background=colors[0], foreground=colors[8]
)

extension_defaults = widget_defaults.copy()

screens = []

for monitor in range(monitors):
    if monitor == 0:
        screens.append(
            Screen(
                top=bar.Bar(
                    [
                        widget.CurrentLayoutIcon(
                            scale=0.5,
                            custom_icon_paths=[
                                os.path.expanduser("~/.config/qtile/icons")
                            ],
                        ),
                        widget.GroupBox(
                            disable_drag=True,
                            # block_highlight_text_color= '000000',
                            # active = 'FFFFFF',
                            hide_unused=True,
                            highlight_method="line",
                            highlight_color=colors[0],
                            borderwidth=2,
                            this_screen_border=colors[8][0],
                            this_current_screen_border=colors[4][0],
                            active=colors[8][0],
                            inactive=colors[8][0],
                        ),
                        sep,
                        mail,
                        sep,
                        updates,
                        sep,
                        news,
                        sep,
                        appointments,
                        sep,
                        todos,
                        music,
                        widget.Spacer(),
                        widget.WindowName(
                            width=bar.CALCULATED, only_current_screen=True
                        ),
                        widget.Spacer(),
                        xbacklight,
                        sep,
                        # vol_text,
                        # vol,
                        volume,
                        sep,
                        battery,
                        sep,
                        clock,
                        sep,
                        systray,
                    ],
                    24,
                ),
                bottom=bar.Bar(
                    [
                        # covid,
                        # sep,
                        # weather,
                        # widget.Spacer(),
                        # widget.Chord(width=bar.CALCULATED),
                        widget.WidgetBox(
                            [
                                widget.CPU(),
                                widget.Spacer(),
                                widget.ThermalSensor(),
                                widget.Spacer(),
                                widget.Memory(),
                            ],
                            text_open="",
                            text_closed="",
                        ),
                        widget.WidgetBox(
                            [widget.Spacer(), widget.Chord(), widget.Spacer()],
                            text_open="",
                            text_closed="",
                            name="widgetbox2",
                        ),
                        # widget.Spacer(),
                        # cpu,
                        # sep,
                        # df,
                        # sep,
                        # memory,
                        # sep,
                        # temp_text,
                        # temp]),
                    ],
                    24,
                ),
            )
        )
    else:
        screens.append(
            Screen(
                top=bar.Bar(
                    [
                        widget.CurrentLayoutIcon(
                            scale=0.5,
                            custom_icon_paths=[
                                os.path.expanduser("~/.config/qtile/icons")
                            ],
                        ),
                        widget.GroupBox(
                            disable_drag=True,
                            # block_highlight_text_color= '000000',
                            # active = 'FFFFFF',
                            hide_unused=True,
                            highlight_method="line",
                            highlight_color=colors[0],
                            borderwidth=2,
                            this_screen_border=colors[8][0],
                            this_current_screen_border=colors[4][0],
                            active=colors[8][0],
                            inactive=colors[8][0],
                        ),
                        widget.Spacer(),
                        widget.WindowName(
                            width=bar.CALCULATED,
                            for_current_screen=True,
                            only_current_screen=True,
                        ),
                        widget.Spacer(),
                        clock,
                    ],
                    24,
                ),
                bottom=bar.Bar(
                    [
                        # covid,
                        # sep,
                        # weather,
                        widget.Spacer(),
                        widget.Chord(width=bar.CALCULATED),
                        widget.WidgetBox(
                            [widget.CPU(), widget.ThermalSensor()],
                            text_open="",
                            text_closed="",
                        ),
                        widget.Spacer(),
                        # cpu,
                        # sep,
                        # df,
                        # sep,
                        # memory,
                        # sep,
                        # temp_text,
                        # temp]),
                    ],
                    24,
                ),
            )
        )

# Drag floating layouts.
mouse = [
    EzDrag(
        "M-1", lazy.window.set_position_floating(), start=lazy.window.get_position()
    ),
    EzDrag("M-3", lazy.window.set_size_floating(), start=lazy.window.get_size()),
    EzClick("M-2", lazy.window.bring_to_front()),
]

@hook.subscribe.startup
def hide_bottom_bar():
    for screen in qtile.screens:
        bar = getattr(screen, "bottom")  # Copyright (c) 2008, 2010 Aldo Cortesi
        bar.show(False)


@hook.subscribe.client_new
def set_parent(window):
    client_by_pid = {}
    for client in qtile.windows_map.values():
        client_pid = client.window.get_net_wm_pid()
        client_by_pid[client_pid] = client

    pid = window.window.get_net_wm_pid()
    ppid = psutil.Process(pid).ppid()
    while ppid:
        window.parent = client_by_pid.get(ppid)
        if window.parent:
            return
        ppid = psutil.Process(ppid).ppid()


@hook.subscribe.client_new
def swallow(window):
    # if not window.floating:
    # if not qtile.current_window.floating:
    if window.name != "Figure 1":
        if window.parent:
            window.parent.minimized = True


@hook.subscribe.client_killed
def unswallow(window):
    if window.parent:
        window.parent.minimized = False


@hook.subscribe.client_killed
def update_widgets_on_kill(window):
    if window.name == "neomutt":
        # qtile.widgets_map['mail'].update(get_mail())
        qtile.widgets_map["mail"].tick()
        qtile.widgets_map["todos"].tick()
    elif window.name == "newsboat":
        # qtile.widgets_map['news'].update(get_news())
        qtile.widgets_map["news"].tick()
    elif window.name == "calcurse":
        qtile.widgets_map["todos"].tick()
        qtile.widgets_map["appointments"].tick()


@hook.subscribe.screen_change
def set_screens(event):
    # subprocess.run(["autorandr", "--change"])
    lazy.spawn("mydock")
    qtile.restart()


# @hook.subscribe.startup_complete
# def update_widgets():
#     qtile.widgets_map['covid'].tick()
#     # qtile.widgets_map['weather'].update()


@hook.subscribe.float_change
def center_window():
    client = qtile.current_window
    if not client.floating:
        return

    screen_rect = qtile.current_screen.get_rect()

    center_x = screen_rect.x + screen_rect.width / 2
    center_y = screen_rect.y + screen_rect.height / 2

    x = center_x - client.width / 2
    y = center_y - client.height / 2

    # don't go off the right...
    x = min(x, screen_rect.x + screen_rect.width - client.width)
    # or left...
    x = max(x, screen_rect.x)
    # or bottom...
    y = min(y, screen_rect.y + screen_rect.height - client.height)
    # or top
    y = max(y, screen_rect.y)

    client.x = int(round(x))
    client.y = int(round(y))
    qtile.current_group.layout_all()


@hook.subscribe.client_focus
def float_to_front(window):
    for window in qtile.current_group.windows:
        if window.floating:
            window.cmd_bring_to_front()


@hook.subscribe.enter_chord
def show_bottom_bar(hook):
    bar = getattr(qtile.current_screen, "bottom")
    qtile.widgets_map["widgetbox2"].cmd_toggle()
    bar.show()


@hook.subscribe.leave_chord
def hide_chord_bar():
    bar = getattr(qtile.current_screen, "bottom")
    qtile.widgets_map["widgetbox2"].cmd_toggle()
    bar.show(False)

dgroups_key_binder = None
dgroups_app_rules = []  # type: List
main = None  # WARNING: this is deprecated and will be removed soon
follow_mouse_focus = True
bring_front_click = False
cursor_warp = False
floating_layout = layout.Floating(
    float_rules=[
        # Run the utility of `xprop` to see the wm class and name of an X client.
        *layout.Floating.default_float_rules,
        Match(wm_class="confirmreset"),  # gitk
        Match(wm_class="makebranch"),  # gitk
        Match(wm_class="maketag"),  # gitk
        Match(wm_class="ssh-askpass"),  # ssh-askpass
        Match(title="branchdialog"),  # gitk
        Match(title="pinentry"),  # GPG key password entry
        Match(wm_class="pinentry-gtk-2"),  # GPG key password entry
        Match(wm_class="skype"),  # GPG key password entry
        Match(wm_class="zoom"),  # GPG key password entry
        Match(wm_class="matplotlib"),  # GPG key password entry
        Match(wm_class="keybindings"),  # GPG key password entry
        Match(title="webcam"),  # GPG key password entry
    ]
)
auto_fullscreen = True
focus_on_window_activation = "focus"

# XXX: Gasp! We're lying here. In fact, nobody really uses or cares about this
# string besides java UI toolkits; you can see several discussions on the
# mailing lists, GitHub issues, and other WM documentation that suggest setting
# this string if your java app doesn't work correctly. We may as well just lie
# and say that we're a working one by default.
#
# We choose LG3D to maximize irony: it is a 3D non-reparenting WM written in
# java that happens to be on java's whitelist.
wmname = "qtile"
