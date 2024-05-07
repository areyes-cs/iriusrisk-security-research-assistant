import warnings

import typer
from bs4 import MarkupResemblesLocatorWarning
from rich import print

from isra.src.component.component import read_current_component, write_current_component, balance_mitigation_values
from isra.src.config.config import get_sf_values
from isra.src.config.constants import CUSTOM_FIELD_STRIDE, CUSTOM_FIELD_SCOPE, \
    CUSTOM_FIELD_BASELINE_STANDARD_REF, CUSTOM_FIELD_BASELINE_STANDARD_SECTION, \
    STRIDE_LIST, CUSTOM_FIELD_AUDIENCE, CUSTOM_FIELD_ATTACK_ENTERPRISE_TECHNIQUE, \
    CUSTOM_FIELD_ATTACK_ENTERPRISE_MITIGATION, PREFIX_COMPONENT_DEFINITION, PREFIX_THREAT, PREFIX_COUNTERMEASURE, \
    IR_SF_C_STANDARD_BASELINES, IR_SF_T_STRIDE, IR_SF_C_SCOPE, IR_SF_C_MITRE, IR_SF_T_MITRE, IR_SF_C_STANDARD_SECTION
from isra.src.utils.cwe_functions import get_original_cwe_weaknesses, get_cwe_description, get_cwe_impact
from isra.src.utils.gpt_functions import query_chatgpt, get_prompt
from isra.src.utils.questionary_wrapper import qselect, qconfirm, qtext
from isra.src.utils.text_functions import extract_json, closest_number, beautify, get_company_name_prefix, \
    check_valid_value

warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

app = typer.Typer(no_args_is_help=True, add_help_option=False)


# Get functions
def get_threat():
    template = read_current_component()

    messages = [
        {"role": "system", "content": get_prompt("generate_threat")},
        {"role": "user", "content": template["component"]["name"] + ":" + template["component"]["desc"]}
    ]

    return query_chatgpt(messages)


def get_threat_description(text, extra):
    messages = [
        {"role": "system", "content": get_prompt("generate_threat_description")},
        {"role": "user", "content": text},
        {"role": "user", "content": extra}
    ]

    return query_chatgpt(messages)


def get_control(threat_base):
    messages = [
        {"role": "system", "content": get_prompt("generate_control")},
        {"role": "user", "content": threat_base["name"] + ":" + threat_base["desc"]}
    ]

    return query_chatgpt(messages)


def get_control_description(text, extra):
    messages = [
        {"role": "system", "content": get_prompt("generate_control_description")},
        {"role": "user", "content": text},
        {"role": "user", "content": extra}
    ]

    return query_chatgpt(messages)


def get_question_description(text):
    messages = [
        {"role": "system", "content": get_prompt("create_description_for_question")},
        {"role": "user", "content": text}
    ]

    return query_chatgpt(messages)


def get_question(item):
    text = item["name"] + ": " + beautify(item["desc"])
    messages = [
        {"role": "system", "content": get_prompt("generate_question")},
        {"role": "user", "content": text}
    ]

    result = query_chatgpt(messages)
    if "\"" in result:
        print(f"Original question was: {result}")
        result = result.replace("\"", "'")
        print(f"Double quotes have been removed: {result}")

    return result


def get_stride_category(item):
    text = item["name"] + ": " + beautify(item["desc"])
    messages = [
        {"role": "system", "content": get_prompt("stride_category")},
        {"role": "user", "content": text}
    ]

    result = query_chatgpt(messages)
    return check_valid_value(result, IR_SF_T_STRIDE)


def get_attack_technique(item):
    text = item["name"] + ": " + beautify(item["desc"])
    messages = [
        {"role": "system",
         "content": get_prompt("attack_technique")},
        {"role": "user", "content": text}
    ]

    result = query_chatgpt(messages)
    return check_valid_value(result, IR_SF_T_MITRE)


def get_attack_mitigation(item):
    text = item["name"] + ": " + beautify(item["desc"])
    messages = [
        {"role": "system", "content": get_prompt("attack_mitigation")},
        {"role": "user", "content": text}
    ]

    result = query_chatgpt(messages)
    return check_valid_value(result, IR_SF_C_MITRE)


def get_intended_scope(item):
    text = item["name"] + ": " + beautify(item["desc"])
    messages = [
        {"role": "system", "content": get_prompt("intended_scope")},
        {"role": "user", "content": text}
    ]

    result = query_chatgpt(messages)
    return check_valid_value(result, IR_SF_C_SCOPE)


def get_intended_audience(item):
    text = item["name"] + ": " + beautify(item["desc"])
    messages = [
        {"role": "system", "content": get_prompt("intended_audience")},
        {"role": "user", "content": text}
    ]

    return query_chatgpt(messages)


def get_baseline_standard_ref(item):
    text = item["name"] + ": " + beautify(item["desc"])
    messages = [
        {"role": "system", "content": get_prompt("standard_baseline")},
        {"role": "user", "content": text}
    ]

    result = query_chatgpt(messages)
    return check_valid_value(result, IR_SF_C_STANDARD_BASELINES)


def get_baseline_standard_section(item):
    template = read_current_component()
    control_ref = item["ref"]
    standard_reference = template["controls"][control_ref]["customFields"][CUSTOM_FIELD_BASELINE_STANDARD_REF]
    print(f"Standard reference for countermeasure is: {standard_reference}")
    messages = [
        {"role": "system", "content": get_prompt("standard_baseline_section")},
        {"role": "user", "content": f"This is the countermeasure description: {item['desc']}"},
        {"role": "user", "content": f"This is the assigned security standard: {standard_reference}"}
    ]

    result = query_chatgpt(messages)
    return check_valid_value(result, IR_SF_C_STANDARD_SECTION)


def get_cia_triad(item):
    text = item["name"] + ": " + beautify(item["desc"])
    messages = [
        {"role": "system", "content": get_prompt("cia_values")},
        {"role": "user", "content": text}
    ]

    return query_chatgpt(messages)


def get_proper_cost(item):
    text = item["name"] + ": " + beautify(item["desc"])
    messages = [
        {"role": "system", "content": get_prompt("get_proper_cost")},
        {"role": "user", "content": text}
    ]

    return query_chatgpt(messages)


def get_proper_cwe(item):
    text = item["name"] + ": " + beautify(item["desc"])
    messages = [
        {"role": "system", "content": get_prompt("cwe_weakness")},
        {"role": "user", "content": text}
    ]

    return query_chatgpt(messages)


def get_all_threats(field=""):
    """This function returns all threats.
    If a custom field is passed it will return those threats that don't have this custom field in place
    This is because we assume that those elements are still pending to be analyzed"""
    threats = dict()

    template = read_current_component()

    for ref, item in template["threats"].items():
        # If there is no custom field with the name indicated in the field parameter
        if not any(cf_ref == field for cf_ref in item["customFields"] if cf_ref != ""):
            # What the user will see when doing the screening
            threats[ref] = item
        # If there is a field but it's empty
        if any(cf_ref == field and cf_value == "" for cf_ref, cf_value in item["customFields"].items() if cf_ref != ""):
            threats[ref] = item

    return threats


def get_all_controls(field=""):
    """This function returns all controls.
    If a custom field is passed it will return those controls that don't have this custom field in place
    This is because we assume that those elements are still pending to be analyzed"""
    controls = dict()

    template = read_current_component()

    for ref, item in template["controls"].items():
        # If there is no custom field with the name indicated in the field parameter
        if not any(cf_ref == field for cf_ref in item["customFields"] if cf_ref != ""):
            # What the user will see when doing the screening
            controls[ref] = item
        # If there is a field but it's empty
        if any(cf_ref == field and cf_value == "" for cf_ref, cf_value in item["customFields"].items() if cf_ref != ""):
            controls[ref] = item

    return controls


def get_complete_threat(item):
    text = item["name"] + ": " + beautify(item["desc"])
    messages = [
        {"role": "system", "content": get_prompt("get_complete_threat")},
        {"role": "user", "content": text}
    ]

    return query_chatgpt(messages)


def get_complete_control(item):
    text = item["name"] + ": " + beautify(item["desc"])
    messages = [
        {"role": "system", "content": get_prompt("get_complete_control")},
        {"role": "user", "content": text}
    ]

    return query_chatgpt(messages)


# Save functions

def save_threats_custom_fields(field, to_update):
    """
    :param field: the custom field to add or update
    :param to_update: a dictionary that contains the threat/control ref and the value for the custom field
    """
    template = read_current_component()

    for k, v in to_update.items():

        threat_custom_fields = template["threats"][k]["customFields"]
        if field in threat_custom_fields:
            if threat_custom_fields[field] == "":
                threat_custom_fields[field] = v
            else:
                if v not in threat_custom_fields[field]:
                    threat_custom_fields[field] = threat_custom_fields[field] + "||" + v
        else:
            threat_custom_fields[field] = v

    write_current_component(template)


def save_controls_custom_fields(field, to_update):
    """
    :param field: the custom field to add or update
    :param to_update: a dictionary that contains the threat/control ref and the value for the custom field
    """
    template = read_current_component()

    for k, v in to_update.items():
        control_custom_fields = template["controls"][k]["customFields"]
        if field in control_custom_fields:
            if control_custom_fields[field] == "":
                control_custom_fields[field] = v
            else:
                if v not in control_custom_fields[field]:
                    control_custom_fields[field] = control_custom_fields[field] + "||" + v
        else:
            control_custom_fields[field] = v

    write_current_component(template)


def save_threats_to_stride_usecase(to_update=None):
    template = read_current_component()

    for relation in template["relations"]:
        threat_custom_fields = template["threats"][relation["threat"]]["customFields"]
        if CUSTOM_FIELD_STRIDE in threat_custom_fields and len(threat_custom_fields[CUSTOM_FIELD_STRIDE]) > 0:
            if to_update is not None and relation["threat"] in to_update:
                stride_category_initial = to_update[relation["threat"]][0]
            else:
                stride_category_initial = threat_custom_fields[CUSTOM_FIELD_STRIDE][0]

            relation["usecase"] = STRIDE_LIST[stride_category_initial]["ref"]
            if relation["usecase"] not in template["usecases"]:
                template["usecases"][relation["usecase"]] = STRIDE_LIST[stride_category_initial]

    write_current_component(template)


def save_stride_category(to_update):
    save_threats_custom_fields(CUSTOM_FIELD_STRIDE, to_update)
    save_threats_to_stride_usecase(to_update)


def save_attack_technique(to_update):
    save_threats_custom_fields(CUSTOM_FIELD_ATTACK_ENTERPRISE_TECHNIQUE, to_update)


def save_attack_mitigation(to_update):
    save_controls_custom_fields(CUSTOM_FIELD_ATTACK_ENTERPRISE_MITIGATION, to_update)


def save_intended_scope(to_update):
    save_controls_custom_fields(CUSTOM_FIELD_SCOPE, to_update)


def save_intended_audience(to_update):
    save_controls_custom_fields(CUSTOM_FIELD_AUDIENCE, to_update)


def save_baseline_standard_ref(to_update):
    save_controls_custom_fields(CUSTOM_FIELD_BASELINE_STANDARD_REF, to_update)


def save_baseline_standard_section(to_update):
    save_controls_custom_fields(CUSTOM_FIELD_BASELINE_STANDARD_SECTION, to_update)


def save_cia_triad(to_update):
    template = read_current_component()

    for k, v in to_update.items():
        values = extract_json(to_update[k])

        template["threats"][k]["riskRating"]["C"] = closest_number(values["C"])
        template["threats"][k]["riskRating"]["I"] = closest_number(values["I"])
        template["threats"][k]["riskRating"]["A"] = closest_number(values["A"])
        template["threats"][k]["riskRating"]["EE"] = closest_number(values["EE"])

    write_current_component(template)


def save_proper_cost(to_update):
    template = read_current_component()
    for control_ref, cost_value in to_update.items():
        control_item = template["controls"][control_ref]
        control_item["cost"] = str(cost_value)
    write_current_component(template)


def save_proper_cwe(to_update):
    template = read_current_component()

    # TODO: This could be improved by creating a script that generates a file with all the information
    # instead of querying the original document over and over
    original_cwe_weaknesses = get_original_cwe_weaknesses()

    for k, val in to_update.items():

        cwe_id, cwe_name = val.split(":")

        for rel in template["relations"]:
            if rel["control"] == k and cwe_id in original_cwe_weaknesses:
                rel["weakness"] = f"CWE-{cwe_id}"

                final_desc = get_cwe_description(original_cwe_weaknesses, [rel["weakness"]])
                final_impact = get_cwe_impact(original_cwe_weaknesses, cwe_id)

                template["weaknesses"][rel["weakness"]] = {
                    "ref": rel["weakness"],
                    "name": rel["weakness"],  # Before: class_base_weaknesses[cwe_id].attrib["Name"],
                    "desc": final_desc,
                    "impact": final_impact
                }

            elif rel["control"] == k and cwe_id not in original_cwe_weaknesses:
                print(f"Weakness {cwe_id} has not been found in the internal CWE list")

    # Cleaning unused weaknesses
    available_weaknesses = set(rel["weakness"] for rel in template["relations"])
    template["weaknesses"] = {w: template["weaknesses"][w] for w in template["weaknesses"] if w in available_weaknesses}

    write_current_component(template)


def save_question(to_update):
    template = read_current_component()

    for control_ref, question_text in to_update.items():
        control_item = template["controls"][control_ref]

        question_desc = ""  # create_description_for_question(question_text)

        control_item["question"] = question_text
        control_item["question_desc"] = question_desc

    write_current_component(template)


def save_complete_threat(to_update):
    template = read_current_component()

    for k, v in to_update.items():
        values = extract_json(to_update[k])

        template["threats"][k]["riskRating"]["C"] = closest_number(values["C"])
        template["threats"][k]["riskRating"]["I"] = closest_number(values["I"])
        template["threats"][k]["riskRating"]["A"] = closest_number(values["A"])
        template["threats"][k]["riskRating"]["EE"] = closest_number(values["EE"])
        template["threats"][k]["customFields"][CUSTOM_FIELD_STRIDE] \
            = check_valid_value(values["stride"], IR_SF_T_STRIDE)
        template["threats"][k]["customFields"][CUSTOM_FIELD_ATTACK_ENTERPRISE_TECHNIQUE] \
            = check_valid_value(values["attack"], IR_SF_T_MITRE)

    write_current_component(template)
    save_threats_to_stride_usecase()


def save_complete_control(to_update):
    template = read_current_component()
    original_cwe_weaknesses = get_original_cwe_weaknesses()

    for k, v in to_update.items():
        values = extract_json(to_update[k])

        template["controls"][k]["question"] = values["question"]
        template["controls"][k]["question_desc"] = ''  # values["question_desc"]
        template["controls"][k]["cost"] = values["cost"]
        template["controls"][k]["customFields"][CUSTOM_FIELD_BASELINE_STANDARD_REF] \
            = check_valid_value(values["baseline"], IR_SF_C_STANDARD_BASELINES)
        template["controls"][k]["customFields"][CUSTOM_FIELD_BASELINE_STANDARD_SECTION] \
            = check_valid_value(values["section"], IR_SF_C_STANDARD_SECTION)
        template["controls"][k]["customFields"][CUSTOM_FIELD_SCOPE] \
            = check_valid_value(values["scope"], IR_SF_C_SCOPE)
        template["controls"][k]["customFields"][CUSTOM_FIELD_ATTACK_ENTERPRISE_MITIGATION] \
            = check_valid_value(values["attack-mit"], IR_SF_C_MITRE)

        cwe_id, cwe_name = values["CWE"].split(":")
        for rel in template["relations"]:
            if rel["control"] == k and rel["weakness"] == "" and cwe_id in original_cwe_weaknesses:
                rel["weakness"] = f"CWE-{cwe_id}"

                final_desc = get_cwe_description(original_cwe_weaknesses, [rel["weakness"]])
                final_impact = get_cwe_impact(original_cwe_weaknesses, cwe_id)

                template["weaknesses"][rel["weakness"]] = {
                    "ref": rel["weakness"],
                    "name": rel["weakness"],  # Before: class_base_weaknesses[cwe_id].attrib["Name"],
                    "desc": final_desc,
                    "impact": final_impact
                }
            elif rel["control"] == k and rel["weakness"] == "" and cwe_id not in original_cwe_weaknesses:
                print(f"Weakness {cwe_id} has not been found in the internal CWE list")

    write_current_component(template)


# Utils


def validate_item(item):
    """
    A quick validation to check if the element (threat or countermeasure) has the minimum attributes in place
    """
    try:
        assert item["ref"] is not None, "Ref is None"
        assert item["ref"] != "", "Ref is empty"
        assert item["name"] is not None, "Name is None"
        assert item["name"] != "", "Name is empty"
        assert item["desc"] is not None, "Desc is None"
        assert item["desc"] != "", "Desc is empty"

        return ""
    except AssertionError as e:
        return str(e)


# Main processes

def screening(items, ask_function, save_function, choices=None):
    if len(items) <= 0:
        print("No items found to do screening")
    else:
        print(f"[red]Starting screening process for {len(items)} items")
        print("Press 'y' or 'n' and then press Enter")
        print("Press 'again' to ask ChatGPT again and hope for a different answer")
        print("Press 'skip' to skip item")
        print("Press 'exit' to stop the screening process without saving any values")
        print("Press 'save' to stop the screening process and save values")

        to_update = dict()

        for index, item in enumerate(items):
            # First we check if the element is valid
            validation = validate_item(items[item])
            if validation != "":
                print(f"Item {item} is not valid: {validation}")
                continue

            # We enter in an infinite loop to keep asking if the user selects 'again'
            # Any other value will break the loop
            while True:
                print(f"Item {index + 1}/{len(items)}: {item}")
                print(f"Description: [bright_cyan]{items[item]['desc']}")
                chatgpt_answer = ask_function(items[item])
                print(f"ChatGPT says: [blue]{chatgpt_answer}")

                screening_item_result = qselect("Is it correct?", choices=[
                    "y",
                    "n",
                    "skip",
                    "again",
                    "exit",
                    "save"
                ])

                if screening_item_result is None:
                    raise typer.Exit(-1)
                elif screening_item_result == "y":
                    print("And another one bites the dust")
                    to_update[item] = chatgpt_answer
                    break
                elif screening_item_result == "n":
                    if choices is not None:
                        manual_answer = qselect("Set manually:", choices=choices)
                        if manual_answer is None:
                            raise typer.Exit(-1)
                        to_update[item] = manual_answer
                        print("And another one bites the dust")
                    else:
                        print("And another one gone")
                    break
                elif screening_item_result == "again":
                    # We don't do anything
                    pass
                elif screening_item_result == "skip":
                    print("And another one gone")
                    break
                elif screening_item_result == "exit":
                    print("Stopping the screening process")
                    # Add something to manually decide
                    return
                elif screening_item_result == "save":
                    print("Saving screening results")
                    save_function(to_update)
                    return

        save_results = qconfirm("No more items. Do you want to save?")
        if save_results:
            print("Saving screening results")
            save_function(to_update)


def threat_generator():
    """
    This is a generator that will help the user to create a threat or a countermeasure
    :return:
    """

    new_threat = {
        "ref": "",
        "name": "",
        "desc": "",
        "customFields": {},
        "references": [],
        "riskRating": {
            "C": "100",
            "I": "100",
            "A": "100",
            "EE": "100"
        }
    }

    # Let's try to find a threat, we'll ask ChatGPT to generate a possible threat name
    while True:

        chatgpt_answer = get_threat()
        print(f"ChatGPT says: [blue]{chatgpt_answer}")
        answer = qconfirm("What do you think?")

        if answer is None:
            raise typer.Exit(-1)
        elif answer:
            new_threat["name"] = chatgpt_answer
            break
        elif not answer:
            print("Let's try again")

    # If the name sounds good, we'll ask ChatGPT to create a description and iterate until we are happy with it
    extra = ""
    while True:
        extra = "" if extra is None else extra

        chatgpt_answer = get_threat_description(new_threat["name"], extra)
        print(f"ChatGPT says: [blue]{chatgpt_answer}")
        answer = qconfirm("What do you think?")

        if answer is None:
            raise typer.Exit(-1)
        elif answer:
            new_threat["desc"] = chatgpt_answer
            break
        elif not answer:
            extra = qtext("Add more information if needed for the next time: ", default=extra)
            print("Let's try again")

    # Finally we add the new threat to our threat collection, but we need a threat ref
    template = read_current_component()
    component_ref = template["component"]["ref"]
    component_ref_nocd = component_ref.replace(PREFIX_COMPONENT_DEFINITION + get_company_name_prefix(), "")

    # Number of manual threats until now + 1
    i = sum(1 for t in template["threats"] if "-MANUAL-" in t) + 1

    new_threat["ref"] = f"{PREFIX_THREAT}{component_ref_nocd}-MANUAL-T{i}"
    template["threats"][new_threat["ref"]] = new_threat

    save_results = qconfirm("Do you want to save?")
    if save_results:
        print("Saving generated results")
        write_current_component(template)


def control_generator():
    """
    This is a generator that will help the user to create a threat or a countermeasure
    :return:
    """

    template = read_current_component()
    component_ref = template["component"]["ref"]
    component_ref_nocd = component_ref.replace(PREFIX_COMPONENT_DEFINITION + get_company_name_prefix(), "")

    selected_threat = qselect("Choose a threat to find a countermeasure", choices=template["threats"].keys())
    threat_item = template["threats"][selected_threat]

    new_control = {
        "ref": "",
        "name": "",
        "desc": "",
        "cost": "2",
        "question": "",
        "question_desc": "",
        "dataflow_tags": [],
        "customFields": dict(),
        "references": [],
        "standards": [],
        "weaknesses": []
    }

    # Let's try to find a threat, we'll ask ChatGPT to generate a possible control name
    while True:
        chatgpt_answer = get_control(threat_item)
        print(f"ChatGPT says: [blue]{chatgpt_answer}")
        answer = qconfirm("What do you think?")

        if answer is None:
            raise typer.Exit(-1)
        elif answer:
            new_control["name"] = chatgpt_answer
            break
        elif not answer:
            print("Let's try again")

    # If the name sounds good, we'll ask ChatGPT to create a description and iterate until we are happy with it
    extra = ""
    while True:
        extra = "" if extra is None else extra

        chatgpt_answer = get_control_description(new_control["name"], extra)
        print(f"ChatGPT says: [blue]{chatgpt_answer}")
        answer = qconfirm("What do you think?")

        if answer is None:
            raise typer.Exit(-1)
        elif answer:
            new_control["desc"] = chatgpt_answer
            break
        elif not answer:
            extra = qtext("Add more information if needed for the next time: ", default=extra)
            print("Let's try again")

    # Finally we add the new threat to our control collection, but we need a control ref

    i = sum(1 for t in template["controls"] if "-MANUAL-" in t) + 1

    new_control["ref"] = f"{PREFIX_COUNTERMEASURE}{component_ref_nocd}-MANUAL-C{i}"
    template["controls"][new_control["ref"]] = new_control

    new_relation = {
        "riskPattern": template["riskPattern"]["ref"],
        "usecase": "General",
        "threat": threat_item["ref"],
        "weakness": "",
        "control": new_control["ref"]
    }
    template["relations"].append(new_relation)

    save_results = qconfirm("Do you want to save?")
    if save_results:
        print("Saving generated results")
        write_current_component(template)
        balance_mitigation_values()


# Commands

@app.callback()
def callback():
    """
    Screening processes
    """


@app.command()
def stride():
    """
    Adds a STRIDE category to a threat
    """
    items = get_all_threats()
    screening(items, get_stride_category, save_stride_category, choices=get_sf_values(IR_SF_T_STRIDE))


@app.command()
def attack():
    """
    Adds a Mitre ATT&CK technique reference to a threat
    """
    items = get_all_threats()
    screening(items, get_attack_technique, save_attack_technique)


@app.command()
def attack_mit():
    """
    Adds a Mitre ATT&CK Mitigation reference to a countermeasure
    """
    items = get_all_controls()
    screening(items, get_attack_mitigation, save_attack_mitigation)


@app.command()
def scope():
    """
    Adds an intended scope for a countermeasure
    """
    items = get_all_controls()
    screening(items, get_intended_scope, save_intended_scope, choices=get_sf_values(IR_SF_C_SCOPE))


# Disabled
# @app.command()
def audience():
    """
    Adds an intended audience for a countermeasure
    """
    items = get_all_controls()
    screening(items, get_intended_audience, save_intended_audience)


@app.command()
def baselines():
    """
    Set baseline standards for countermeasures
    """
    items = get_all_controls()
    screening(items, get_baseline_standard_ref, save_baseline_standard_ref,
              choices=get_sf_values(IR_SF_C_STANDARD_BASELINES))


@app.command()
def sections():
    """
    Set baseline standards sections for countermeasures
    """
    items = get_all_controls()
    screening(items, get_baseline_standard_section, save_baseline_standard_section)


@app.command()
def cia():
    """
    Adds CIA values for threats
    """
    items = get_all_threats()
    screening(items, get_cia_triad, save_cia_triad)


@app.command()
def cost():
    """
    Adds cost values for countermeasures
    """
    items = get_all_controls()
    screening(items, get_proper_cost, save_proper_cost, choices=[
        "0",
        "1",
        "2"
    ])


@app.command()
def cwe():
    """
    Finds best CWE weakness for a countermeasure
    """

    items = get_all_controls()
    screening(items, get_proper_cwe, save_proper_cwe)


@app.command()
def question():
    """Creates a set of questions for the countermeasures in a component that will change the status
     depending on the given answer"""

    items = get_all_controls()
    screening(items, get_question, save_question)


@app.command()
def new_threat():
    """
    Generates a threat based on the current component name and description
    """
    threat_generator()


@app.command()
def new_control():
    """
    Generates a countermeasure based on the current component name and description
    """
    control_generator()


@app.command()
def threat_screening():
    """
    Does all threat screenings at the same time
    """
    items = get_all_threats()
    screening(items, get_complete_threat, save_complete_threat)


@app.command()
def control_screening():
    """
    Does all countermeasure screenings at the same time
    """
    items = get_all_controls()
    screening(items, get_complete_control, save_complete_control)
