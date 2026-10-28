import nbformat
from nbclient import NotebookClient

# Most protocols are run from Jupyter, where MechWolf applies nest_asyncio
# at import and schedules the run on the kernel's event loop instead of
# calling asyncio.run(), so that path needs its own test.

RUN_PROTOCOL = """
import asyncio

import mechwolf as mw

a = mw.Vessel(name="a", description="nothing")
pump = mw.DummyPump(name="Dummy pump")
sensor = mw.DummySensor(name="sensor")
tube = mw.Tube("1 foot", "1/16 in", "2/16 in", "PVC")

A = mw.Apparatus()
A.add(a, pump, tube)
A.add(pump, sensor, tube)

P = mw.Protocol(A, name="notebook execution")
P.add(pump, rate="5 mL/min", start="0 seconds", stop="1 secs")
P.add(sensor, rate="5 Hz", start="0 secs", stop="1 secs")

E = P.execute(confirm=True, dry_run=True, log_file=None, data_file=None)
"""

CHECK_RESULT = """
for _ in range(300):
    if E.was_executed:
        break
    await asyncio.sleep(0.1)

assert E.was_executed
assert len(E.data["sensor"]) >= 5, E.data
assert E.data["sensor"][0].data == "simulated read"
assert pump.rate == mw._ureg.parse_expression(pump._base_state["rate"])
"""


def test_protocol_runs_in_a_notebook():
    nb = nbformat.v4.new_notebook()
    nb.cells = [
        nbformat.v4.new_code_cell(RUN_PROTOCOL),
        nbformat.v4.new_code_cell(CHECK_RESULT),
    ]
    NotebookClient(nb, timeout=120, kernel_name="python3").execute()
