
import html
import json

from ..login import *

class InfoBotCourseRegisterWrapper:





(helper.graduate() ? CR_SEARCH_YJS_URL : CR_SEARCH_URL, {
            m: "kylSearch",
            page: page ?? -1,
            "p_sort.p1": "",
            "p_sort.p2": "",
            "p_sort.asc1": "true",
            "p_sort.asc2": "true",
            p_xnxq: semester,
            pathContent: "课余量查询",
            p_kch: id ?? "",
            p_kxh: "",
            p_kcm: name ?? "",
            p_skxq: dayOfWeek ?? "",
            p_skjc: period ?? "",
            goPageNumber: page ?? 1,
        }, "GBK")