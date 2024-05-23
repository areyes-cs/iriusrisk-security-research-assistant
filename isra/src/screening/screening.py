import typer

from isra.src.config.config import get_sf_values
from isra.src.config.constants import IR_SF_T_STRIDE, IR_SF_C_SCOPE, IR_SF_C_STANDARD_BASELINES
from isra.src.screening.screening_service import get_all_threats, screening, get_stride_category, save_stride_category, \
    get_attack_technique, save_attack_technique, get_attack_mitigation, save_attack_mitigation, get_all_controls, \
    get_intended_scope, save_intended_scope, get_baseline_standard_ref, save_baseline_standard_ref, \
    get_baseline_standard_section, save_baseline_standard_section, get_cia_triad, save_cia_triad, get_proper_cost, \
    save_proper_cost, get_proper_cwe, save_proper_cwe, generate_question, save_question, threat_generator, \
    control_generator, autoscreening_init, fix_component

app = typer.Typer(no_args_is_help=True, add_help_option=False)


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
    screening(items, generate_question, save_question)


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
def autoscreening():
    """
    Automated screening process
    """
    autoscreening_init()


@app.command()
def fix():
    """
    Tries to fix anything that doesn't fit the YSC schema
    """
    fix_component()
