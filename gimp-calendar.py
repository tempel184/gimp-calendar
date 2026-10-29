#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#    This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.

import gi
gi.require_version('Gimp', '3.0')
from gi.repository import Gimp
gi.require_version('GimpUi', '3.0')
from gi.repository import GimpUi
gi.require_version('Gegl', '0.4')
from gi.repository import Gegl
from gi.repository import GObject
from gi.repository import GLib
from gi.repository import Gio

import os
import sys
import datetime

def N_(message): return message
def _(message): return GLib.dgettext(None, message)

PROC_NAME = 'plug-in-calendar-python'


holiday_map = [
    { "MONTH" :  1, "DAY" :  1, "COMMENT" : "元旦" },
    { "MONTH" :  1, "WEEKS" : 2, "WEEKDAY" : 1, "COMMENT" : "成人の日" },
    { "MONTH" :  2, "DAY" : 11, "COMMENT" : "建国記念日" },
    { "MONTH" :  2, "DAY" : 23, "COMMENT" : "天皇誕生日" },
    { "MONTH" :  3, "DAY" :  0, "IS_SPDAY" : 1, "COMMENT" : "春分の日" },
    { "MONTH" :  4, "DAY" : 29, "COMMENT" : "昭和の日" },
    { "MONTH" :  5, "DAY" :  3, "COMMENT" : "憲法記念日" },
    { "MONTH" :  5, "DAY" :  4, "COMMENT" : "みどりの日" },
    { "MONTH" :  5, "DAY" :  5, "COMMENT" : "こどもの日" },
    { "MONTH" :  7, "WEEKS" : 3, "WEEKDAY" : 1, "COMMENT" : "海の日" },
    { "MONTH" :  8, "DAY" : 11, "COMMENT" : "山の日" },
    { "MONTH" :  9, "WEEKS" : 3, "WEEKDAY" : 1, "COMMENT" : "敬老の日" },
    { "MONTH" :  9, "DAY" :  0, "IS_EQDAY" : 1, "COMMENT" : "秋分の日" },
    { "MONTH" : 10, "WEEKS" : 2, "WEEKDAY" : 1, "COMMENT" : "スポーツの日" },
    { "MONTH" : 11, "DAY" :  3, "COMMENT" : "文化の日" },
    { "MONTH" : 11, "DAY" : 23, "COMMENT" : "勤労感謝の日" }
]

holiday_map_color = [
    "#000000",
    "#00ffff",
    "#ff0000",
    "#ff0000"
]

def python_calendar_setup(image, pos):
    #Gimp.message("image size %d %d" % (image.width, image.height))
    #Gimp.message("box_pos %d" % (pos))

    i_width = image.get_width()
    i_height = image.get_height()
    # 4分割 + 90%
    y_width = i_width * 9 / 20
    y_height = i_height * 9 / 20
    # フォントサイズ
    y_point_w = y_width / 15 # 30文字
    y_point_h = y_height / 10 # 10行 -> 8行？
    wf_point = (y_point_h if y_point_w > y_point_h else y_point_w) - 1
    # padding 5px
    box_width = wf_point * 15 + 10
    box_height = wf_point * 10 + 10
    #Gimp.message("box size %d %d" % (box_width, box_height))
    x_step = (box_width - 5) / 7
    y_step = (box_height - 5) / 8
    # 四隅
    delta_x = (i_width / 4 - box_width / 2) + (i_width / 2 * (pos % 2))
    delta_y = (i_height / 4 - box_height / 2) + (i_height / 2 * int(pos / 2))
    #Gimp.message("box postion %d %d" % (delta_x, delta_y))
    # フォントの再計算 80%
    wf_point = wf_point * 0.9 # 90%?
    #Gimp.message("font size %d" % (wf_point))

    box = {
        "width": box_width, "height": box_height,
        "step_x": x_step, "step_y": y_step,
        "delta_x": delta_x, "delta_y": delta_y,
        "wf_point": wf_point
    }
    Gimp.message("box layer %r" % (box))
    return box


def python_calender_base(image, box, color, bgFont, fgFont, year, month):
    layer = Gimp.Layer.new(image, "Base", box["width"], box["height"],
        Gimp.ImageType.RGB_IMAGE, 50, Gimp.LayerMode.NORMAL)
    image.insert_layer(layer, None, 0)
    layer.fill(Gimp.FillType.WHITE) # (gimp-drawable-fill bx-layer 2)
    layer.set_offsets(box["delta_x"], box["delta_y"])

    # 月
    Gimp.context_set_foreground(color)
    f_size = box["width"] * 0.64
    # PIXELS := 0
    #month_layer = pdb.gimp_text_fontname(image, None, 0, 0, "%d" % (month), -1, True, f_size, PIXELS, bgFont)
    month_layer = Gimp.text_font(image, None, 0, 0, f'{month}', -1, True, f_size, bgFont)
    m_x = (box["width"] / 2) - (month_layer.get_width() / 2) + 5
    m_y = (box["height"] / 2) - (month_layer.get_height() / 2) + 5
    month_layer.set_offsets(box["delta_x"] + m_x, box["delta_y"] + m_y)
    #pdb.gimp_image_set_active_layer(image, month_layer)

    # 月/文字
    month_strs = ["January", "February", "March", "April", "May", "June",
                "July", "August", "September", "October", "November", "December"]
    #python_calendar_debug("data %r %r" % (year, month))

    month_str = "%s, %d" % (month_strs[int(month) - 1], year)
    #month_layer_s = pdb.gimp_text_fontname(image, None, 0, 0, month_str, -1, True, box["wf_point"], PIXELS, bgFont)
    month_layer_s = Gimp.text_font(image, None, 0, 0, month_str, -1, True, box["wf_point"], bgFont)
    m_y = box["step_y"] - month_layer_s.get_height() - 5
    #python_calendar_debug("font height:%d" % (month_layer_s.height))
    month_layer_s.set_offsets(box["delta_x"] + 10, box["delta_y"] + 5)

    # レイヤー統合
    # EXPAND_AS_NECESSARY := 0
    #month_layer = pdb.gimp_image_merge_down(image, month_layer_s, 0)
    month_layer_n = Gimp.Image.merge_down(image, month_layer_s, Gimp.MergeType.EXPAND_AS_NECESSARY)
    month_layer_n.set_name("month")
    #month_layer.name = "month"
    #pdb.gimp_image_set_active_layer(image, month_layer)

    # 曜日
    week_strs = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
    silver = Gegl.Color.new("sliver")
    silver.set_rgba(0.5, 0.5, 0.5, 1.0)
    #gimp.set_foreground(128, 128, 128)
    Gimp.context_set_foreground(silver)

    s_y = box["step_y"] + 10
    for i in range(1,8):
        #wd_layer = pdb.gimp_text_fontname(image, None, 0, 0, week_strs[i - 1], -1, True, box["wf_point"] * 0.9, PIXELS, bgFont)
        wd_layer = Gimp.text_font(image, None, 0, 0, week_strs[i - 1], -1, True, box["wf_point"] * 0.9, bgFont)
        #s_x = (((i * 2) - 1 * box["step_x"]) / 2) - (wd_layer.width / 2) + 5
        s_x = (box["step_x"] * i - (box["step_x"] / 2)) - (wd_layer.get_width() / 2) + 5
        #python_calendar_debug("x: i:%d height:%d" % (i, s_x))
        wd_layer.set_offsets(box["delta_x"] + s_x , box["delta_y"] + s_y)

        if i > 1:
            #nwd_layer = pdb.gimp_image_merge_down(image, wd_layer, 0)
            nwd_layer = Gimp.Image.merge_down(image, wd_layer, Gimp.MergeType.EXPAND_AS_NECESSARY)


def setup_month_days(year, month):
    first = datetime.date(year, month, 1)
    loop_first = first - datetime.timedelta(days = 8)
    loop_end = first + datetime.timedelta(days = 40)
    Gimp.message(f'{year}/{month} {loop_first} to {loop_end}')

    # 春分,秋分は再計算(1980-2099)
    for h in holiday_map:
        if 'IS_SPDAY' in h and h["IS_SPDAY"] == 1:
            sp_day = int((year - 1980) * 0.242194 + 20.8431) - int((year - 1980) / 4)
            h["DAY"] = sp_day

        if 'IS_EQDAY' in h and h["IS_EQDAY"] == 1:
            eq_day = int((year - 1980) * 0.242194 + 23.2488) - int((year - 1980) / 4)
            h["DAY"] = eq_day
    #Gimp.message(f'{holiday_map}')

    # 曜日, 祝日
    days = []
    loop_date = loop_first
    while loop_date <= loop_end:
        d_info = { "YEAR": loop_date.year, "MONTH": loop_date.month, "DAY": loop_date.day,
            "WEEKDAY": loop_date.isoweekday(), # 曜日 1:月..7:日
            "WEEKS": int((loop_date.day - 1) / 7) + 1, # 第n週
            "HOLIDAY": 0, # 平日,土曜日,日曜日,祝日, etc
            #"IS_SUBHOLIDAY": 0, # 振り替え
            "VIEW_FLAG": 0, # パレット番号
            "VIEW_X": 0, "VIEW_Y": 0, # 表示位置
        }
        loop_date += datetime.timedelta(days = 1)
        #Gimp.message(f'{d_info}')

        # 土日
        if d_info["WEEKDAY"] == 6:
            d_info["HOLIDAY"] = 1
        if d_info["WEEKDAY"] == 7:
            d_info["HOLIDAY"] = 2

        for h in holiday_map:
            if d_info["MONTH"] != h["MONTH"]:
                continue

            if ('DAY' in h) and d_info["DAY"] == h["DAY"]:
                d_info["HOLIDAY"] = h["FLAG"] if 'FLAG' in h else 3

            if ('WEEKS' in h) and d_info["WEEKS"] == h["WEEKS"] and d_info["WEEKDAY"] == h["WEEKDAY"]:
                d_info["HOLIDAY"] = h["FLAG"] if 'FLAG' in h else 3

        days.append(d_info)
    #Gimp.message(f'{days}')

    # 祝日 - 平日 - 祝日 第3条第3項
    start_i = 0
    end_i = len(days)
    for i in range(1, len(days) - 1):
        if days[i - 1]["HOLIDAY"] == 3 and days[i + 1]["HOLIDAY"] == 3:
            days[i]["HOLIDAY"] = 3

        if days[i]["MONTH"] == month and days[i]["DAY"] == 1:
            start_i = i

        if days[i]["MONTH"] != month and days[i]["DAY"] == 1:
            end_i = i

    # 振替休日 第3条第2項
    is_holiday = False
    for d in days:
        if is_holiday == True and d["HOLIDAY"] != 3:
            d["HOLIDAY"] = 3
            is_holiday = False
            continue

        if is_holiday == False and d["HOLIDAY"] == 3 and d["WEEKDAY"] == 7:
            is_holiday = True
            continue

    start_i -= days[start_i]["WEEKDAY"] % 7
    #end_i += (6 if days[end_i]["WEEKDAY"] == 7 else (6 - days[end_i]["WEEKDAY"]))
    end_i += 7 - days[end_i]["WEEKDAY"]

    # 座標, パレット
    r_days = days[start_i:end_i]
    i = 0
    for d in r_days:
        d["VIEW_X"] = i % 7
        d["VIEW_Y"] = int(i / 7)

        d["VIEW_FLAG"] = d["HOLIDAY"] if d["MONTH"] == month else -1

        i += 1

    #Gimp.message(f'{r_days}')
    return r_days


def python_calendar_draw(image, box, color, pos, fgFont, cals):
    is_down_layer = False
    Gimp.message('begin')
    for cal in cals:
        Gimp.message(f'{cal}')
        if cal["VIEW_FLAG"] < 0:
            continue

        #gimp.set_foreground(holiday_map_color[cal["VIEW_FLAG"]])
        c =  Gegl.Color.new(holiday_map_color[cal["VIEW_FLAG"]])
        #Gimp.message(f'{c}')

        Gimp.context_set_foreground(c)
        str = "%d" % cal["DAY"]
        #Gimp.message(f'str={str} {box["wf_point"]} {fgFont}')
        #f_layer = pdb.gimp_text_fontname(image, None, 0, 0, str, -1, True, box["wf_point"], PIXELS, fgFont)
        f_layer = Gimp.text_font(image, None, 0, 0, str, -1, True, box["wf_point"], fgFont)
        #Gimp.message(f'{f_layer}')
        s_x = (box["step_x"] * (cal["VIEW_X"] + 1) - (box["step_x"] / 2)) - (f_layer.get_width() / 2) + 5
        s_y = (box["step_y"] * (cal["VIEW_Y"] + 3) - (box["step_y"] / 2)) - (f_layer.get_height() / 2) + 5
        #f_layer.translate(box["delta_x"] + s_x , box["delta_y"] + s_y)
        f_layer.set_offsets(box["delta_x"] + s_x , box["delta_y"] + s_y)

        if is_down_layer:
            #nwd_layer = pdb.gimp_image_merge_down(image, f_layer, 0)
            nwd_layer = Gimp.Image.merge_down(image, f_layer, Gimp.MergeType.EXPAND_AS_NECESSARY)

        is_down_layer = True


class GCalendar (Gimp.PlugIn):
    ## GimpPlugIn virtual methods ##
    def do_query_procedures(self):
        return [ PROC_NAME ]

    def do_create_procedure(self, name):
        if name != PROC_NAME:
            return None
        Gegl.init(None)
        procedure = Gimp.ImageProcedure.new(self, name,
                                            Gimp.PDBProcType.PLUGIN,
                                            self.run, None)

        procedure.set_image_types("*")
        procedure.set_sensitivity_mask (Gimp.ProcedureSensitivityMask.DRAWABLE)

        procedure.set_menu_label(_("Plug-In Calendar in _Python 3"))
        #procedure.set_icon_name(GimpUi.ICON_GEGL)
        procedure.add_menu_path('<Image>/Filters/Python-Fu')

        procedure.set_documentation(_("Plug-in Calendar in Python 3"),
                                    _("Plug-in Calendar in Python 3"),
                                    name)
        procedure.set_attribution("KOUGABU", "KOUGABU", "2026")

        procedure.add_int_argument('year', '年', None, 2000, 2099, 2026,  GObject.ParamFlags.READWRITE)
        procedure.add_int_argument('month', '月', None, 1, 12, 1,  GObject.ParamFlags.READWRITE)
        black = Gegl.Color.new("black")
        black.set_rgba(0.0, 0.0, 0.0, 1.0)
        procedure.add_color_argument('mcolor', '月の文字色', None, False, black, GObject.ParamFlags.READWRITE)
        procedure.add_font_argument('fgfont', '前景フォント', None, False, None, True, GObject.ParamFlags.READWRITE)
        procedure.add_font_argument('bgfont', '背景フォント', None, False, None, True, GObject.ParamFlags.READWRITE)
        pos = Gimp.Choice.new()
        pos.add("0", 1, "左上", "LeftTop")
        pos.add("1", 2, "右上", "RightTop")
        pos.add("2", 3, "左下", "LeftBottom")
        pos.add("3", 4, "右下", "RightBottom")
        procedure.add_choice_argument('position', '位置', None, pos, '1', GObject.ParamFlags.READWRITE)

        return procedure

    def run(self, procedure, run_mode, image, drawables, config, run_data):
        Gimp.message("begin")

        if len(drawables) != 1:
            msg = _("Procedure '{}' only works with one drawable.").format(procedure.get_name())
            error = GLib.Error.new_literal(Gimp.PlugIn.error_quark(), msg, 0)
            return procedure.new_return_values(Gimp.PDBStatusType.CALLING_ERROR, error)
        else:
            drawable = drawables[0]

        if run_mode == Gimp.RunMode.INTERACTIVE:
            gi.require_version('Gtk', '3.0')
            from gi.repository import Gtk
            gi.require_version('Gdk', '3.0')
            from gi.repository import Gdk

            GimpUi.init("Create Calendar Layer")
            dialog = GimpUi.ProcedureDialog.new(procedure, config, 'Calendar')
            dialog.fill(['year', 'month', 'mcolor', 'fgfont', 'bgfont', 'position'])
            if not dialog.run():
                dialog.destroy()
                return procedure.new_return_values(Gimp.PDBStatusType.CANCEL, None)
            dialog.destroy()

        year = config.get_property('year')
        month = config.get_property('month')
        mcolor = config.get_property('mcolor')
        fgfont = config.get_property('fgfont')
        bgfont = config.get_property('bgfont')
        position = int(config.get_property('position'))
        Gimp.message(f'input: year={year}, month={month}, mcolor={mcolor}, fgfont={fgfont}, bgfont={bgfont}, position={position}')

        box = python_calendar_setup(image, position)
        python_calender_base(image, box, mcolor, bgfont, fgfont, year, month)
        cals = setup_month_days(year, month)
        python_calendar_draw(image, box, mcolor, position, fgfont, cals)

        return procedure.new_return_values(Gimp.PDBStatusType.SUCCESS, GLib.Error())

Gimp.main(GCalendar.__gtype__, sys.argv)
