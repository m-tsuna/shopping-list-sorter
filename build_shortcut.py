"""ショートカット「買い物に追加」のファイルを、Python で組み立てるファイル。

iPhone で部品を1つずつ並べる代わりに、ここで作って署名し、取り込めるようにする。
鍵はファイルに入れず、iPhone で取り込むときに貼り付けてもらう。
"""

import json
import plistlib
import subprocess
import uuid

from config import ASK_EVERY_TIME, BASE_DIR, SETTINGS_FILE

FOLDER = "買い物仕分け"
UNSIGNED_FILE = BASE_DIR / "shortcut_unsigned.shortcut"
SIGNED_FILE = BASE_DIR / "買い物に追加.shortcut"
OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
OBJECT_MARK = "￼"  # 文章の中で変数が入る場所を表す印


def variable(name):
    """変数を指す部品を作る。"""
    return {"Type": "Variable", "VariableName": name}


def attachment(name):
    """アクションの入力に変数を渡す形を作る。"""
    return {"Value": variable(name), "WFSerializationType": "WFTextTokenAttachment"}


def text(*parts):
    """文字と変数を混ぜた文章を作る。変数は ("変数名",) のタプルで渡す。"""
    string, ranges = "", {}
    for part in parts:
        if isinstance(part, tuple):
            ranges[f"{{{len(string)}, 1}}"] = variable(part[0])
            string += OBJECT_MARK
        else:
            string += part
    return {
        "Value": {"string": string, "attachmentsByRange": ranges},
        "WFSerializationType": "WFTextTokenString",
    }


def action(name, **params):
    """アクションを1つ作る。"""
    return {
        "WFWorkflowActionIdentifier": f"is.workflow.actions.{name}",
        "WFWorkflowActionParameters": params,
    }


def with_output(name, variable_name, **params):
    """アクションの結果を、名前を付けた変数に入れる2つの部品を作る。"""
    output_id = str(uuid.uuid4()).upper()
    first = action(name, UUID=output_id, **params)
    output = {
        "Value": {"OutputUUID": output_id, "Type": "ActionOutput", "OutputName": variable_name},
        "WFSerializationType": "WFTextTokenAttachment",
    }
    return [first, action("setvariable", WFVariableName=variable_name, WFInput=output)]


def if_block(condition, then_actions, else_actions=None):
    """「もしも」のまとまりを作る。"""
    group = str(uuid.uuid4()).upper()
    actions = [action("conditional", GroupingIdentifier=group, WFControlFlowMode=0, **condition)]
    actions += then_actions
    if else_actions is not None:
        actions.append(action("conditional", GroupingIdentifier=group, WFControlFlowMode=1))
        actions += else_actions
    actions.append(action("conditional", GroupingIdentifier=group, WFControlFlowMode=2))
    return actions


def has_value(name):
    return {"WFCondition": 100, "WFInput": {"Type": "Variable", "Variable": attachment(name)}}


def no_value(name):
    return {"WFCondition": 101, "WFInput": {"Type": "Variable", "Variable": attachment(name)}}


def equals(name, value):
    return {
        "WFCondition": 4,
        "WFInput": {"Type": "Variable", "Variable": attachment(name)},
        "WFConditionalActionString": value,
    }


def contains(name, other):
    return {
        "WFCondition": 99,
        "WFInput": {"Type": "Variable", "Variable": attachment(name)},
        "WFConditionalActionString": text((other,)),
    }


def set_store(source):
    """変数「お店」に別の変数の値を入れる。"""
    return [action("setvariable", WFVariableName="お店", WFInput=attachment(source))]


def choose_store():
    """お店の一覧から選んでもらう。"""
    return with_output(
        "choosefromlist",
        "選んだお店",
        WFInput=attachment("お店の配列"),
        WFChooseFromListActionPrompt="どのお店ですか？",
    ) + set_store("選んだお店")


def read_file(name, text_var, dict_var):
    """iCloud のファイルを読み、文章と辞書の変数に入れる。"""
    return (
        with_output(
            "documentpicker.open",
            "読んだファイル",
            WFGetFilePath=f"{FOLDER}/{name}",
            WFFileErrorIfNotFound=True,
            WFShowFilePicker=False,
        )
        + with_output("detect.text", text_var, WFInput=attachment("読んだファイル"))
        + with_output("detect.dictionary", dict_var, WFInput=attachment(text_var))
    )


def field(key, value, item_type=0):
    """通信の本文の1項目を作る。item_type は 0 が文字、3 が数値。"""
    return {"WFItemType": item_type, "WFKey": text(key), "WFValue": value}


def dictionary(items):
    return {
        "Value": {"WFDictionaryFieldValueItems": items},
        "WFSerializationType": "WFDictionaryFieldValue",
    }


def ask_ai_actions():
    """OpenAI にお店を聞く部品を作る。ルールに無い品物のときだけ動く。"""
    settings = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    return (
        with_output("text.combine", "お店の一覧", text=attachment("お店の配列"),
                    WFTextSeparator="Custom", WFTextCustomSeparator="、")
        + with_output("getvalueforkey", "聞き方0", WFInput=attachment("設定"),
                      WFGetDictionaryValueType="Value", WFDictionaryKey="prompt")
        + with_output("text.replace", "聞き方1", WFInput=text(("聞き方0",)),
                      WFReplaceTextFind="{stores}", WFReplaceTextReplace=text(("お店の一覧",)))
        + with_output("text.replace", "聞き方2", WFInput=text(("聞き方1",)),
                      WFReplaceTextFind="{examples}", WFReplaceTextReplace=text(("ルール文字",)))
        + with_output("text.replace", "聞き方", WFInput=text(("聞き方2",)),
                      WFReplaceTextFind="{item}", WFReplaceTextReplace=text(("品物",)))
        + with_output(
            "downloadurl",
            "AIの返事",
            WFURL=OPENAI_RESPONSES_URL,
            WFHTTPMethod="POST",
            ShowHeaders=True,
            WFHTTPHeaders=dictionary([field("Authorization", text("Bearer ", ("鍵",)))]),
            WFHTTPBodyType="JSON",
            WFJSONValues=dictionary([
                field("model", text(settings["model"])),
                field("input", text(("聞き方",))),
                field("temperature", text(str(settings["temperature"])), 3),
                field("max_output_tokens", text(str(settings["max_tokens"])), 3),
            ]),
        )
        + with_output("getvalueforkey", "AIの答え", WFInput=attachment("AIの返事"),
                      WFGetDictionaryValueType="Value",
                      WFDictionaryKey="output.1.content.1.text")
    )


def network_check():
    """通信できそうなときだけ、変数「接続の印」に値を入れる。

    通信が失敗するとショートカットごと止まるので、AI に聞く前に確かめる。
    機内モードでも携帯回線の種類は残るので、自分の IP アドレスの有無で判断する。
    """
    mark = with_output("gettext", "接続の印", WFTextActionText="あり")
    return (
        with_output("getipaddress", "IPv4", WFIPAddressSourceOption="Local",
                    WFIPAddressTypeOption="IPv4")
        + with_output("getipaddress", "IPv6", WFIPAddressSourceOption="Local",
                      WFIPAddressTypeOption="IPv6")
        + if_block(has_value("IPv4"), mark)
        + if_block(has_value("IPv6"), mark)
    )


def confirm_menu():
    """「〇〇でいいですか？」のメニューを作る。"""
    group = str(uuid.uuid4()).upper()
    yes, other, always = "はい", "ほかのお店を選ぶ", ASK_EVERY_TIME

    def item(title):
        return action("choosefrommenu", GroupingIdentifier=group, WFControlFlowMode=1,
                      WFMenuItemTitle=title)

    return [
        action("choosefrommenu", GroupingIdentifier=group, WFControlFlowMode=0,
               WFMenuPrompt=text(("AIの答え",), " でいいですか？"), WFMenuItems=[yes, other, always]),
        item(yes), *set_store("AIの答え"),
        item(other), *choose_store(),
        item(always), *choose_store(),
        *with_output("gettext", "覚えるお店", WFTextActionText=ASK_EVERY_TIME),
        action("choosefrommenu", GroupingIdentifier=group, WFControlFlowMode=2),
    ]


def learn_actions():
    """決まったお店をルールに足して保存する。"""
    fill_store = if_block(
        no_value("覚えるお店"),
        [action("setvariable", WFVariableName="覚えるお店", WFInput=attachment("お店"))],
    )
    return fill_store + with_output(
        "setvalueforkey", "新しいルール", WFDictionary=attachment("ルール"),
        WFDictionaryKey=text(("品物",)), WFDictionaryValue=text(("覚えるお店",)),
    ) + [
        action("documentpicker.save", WFInput=attachment("新しいルール"),
               WFAskWhereToSave=False, WFFileDestinationPath=f"{FOLDER}/rules.json",
               WFSaveFileOverwrite=True)
    ]


def build_actions():
    """ショートカット全体の部品を、順番に並べる。"""
    stores = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))["stores"]
    actions = with_output("gettext", "鍵", WFTextActionText="ここに鍵")
    actions += with_output("ask", "品物", WFAskActionPrompt="何を買いますか？", WFInputType="Text")
    actions += if_block(no_value("品物"), [action("exit")])
    actions += read_file("rules.json", "ルール文字", "ルール")
    actions += read_file("settings.json", "設定文字", "設定")
    actions += with_output("getvalueforkey", "お店の配列", WFInput=attachment("設定"),
                           WFGetDictionaryValueType="Value", WFDictionaryKey="stores")
    actions += with_output("getvalueforkey", "決まったお店", WFInput=attachment("ルール"),
                           WFGetDictionaryValueType="Value", WFDictionaryKey=text(("品物",)))
    actions += if_block(
        has_value("決まったお店"),
        with_output("gettext", "決まったお店の名前", WFTextActionText=text(("決まったお店",)))
        + if_block(
            equals("決まったお店の名前", ASK_EVERY_TIME),
            choose_store(),
            set_store("決まったお店"),
        ),
        network_check()
        + if_block(
            has_value("接続の印"),
            ask_ai_actions()
            + if_block(contains("お店の一覧", "AIの答え"), confirm_menu(), choose_store()),
            choose_store(),
        )
        + learn_actions(),
    )
    # 比べるのは文章の変数にする。辞書から来た値のままだと「等しい」の条件が使えない
    actions += with_output("gettext", "お店の名前", WFTextActionText=text(("お店",)))
    for store in stores:
        actions += if_block(
            equals("お店の名前", store),
            [action("addnewreminder", WFCalendarItemTitle=text(("品物",)))],
        )
    actions.append(action("notification", WFNotificationActionBody=text(("お店",), " に ", ("品物",), " を入れました")))
    return actions


def build_workflow():
    """ショートカットのファイル全体を作る。"""
    return {
        "WFWorkflowClientVersion": "2605.0.5",
        "WFWorkflowMinimumClientVersion": 900,
        "WFWorkflowMinimumClientVersionString": "900",
        "WFWorkflowIcon": {"WFWorkflowIconStartColor": 4282601983, "WFWorkflowIconGlyphNumber": 59511},
        "WFWorkflowTypes": [],
        "WFWorkflowInputContentItemClasses": [],
        "WFWorkflowActions": build_actions(),
        # 取り込むときに鍵を聞く。1つ目のアクション（鍵の文字）の中身に入る
        "WFWorkflowImportQuestions": [{
            "ActionIndex": 0,
            "Category": "Parameter",
            "DefaultValue": "",
            "ParameterKey": "WFTextActionText",
            "Text": "OpenAI の鍵を貼り付けてください",
        }],
    }


def main():
    """署名付きのショートカットファイルを作る。"""
    with open(UNSIGNED_FILE, "wb") as file:
        plistlib.dump(build_workflow(), file, fmt=plistlib.FMT_BINARY)
    subprocess.run(
        ["shortcuts", "sign", "--mode", "anyone", "--input", UNSIGNED_FILE, "--output", SIGNED_FILE],
        check=True,
    )
    UNSIGNED_FILE.unlink()
    print(f"作りました：{SIGNED_FILE}")


if __name__ == "__main__":
    main()
