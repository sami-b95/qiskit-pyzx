from collections import OrderedDict

from pyzx.circuit import Circuit
from qiskit.circuit import ClassicalRegister, QuantumCircuit, QuantumRegister
from qiskit.dagcircuit import DAGCircuit

from circuit_translator import check_classical_control, to_pyzx_gate


def dag_to_pyzx_circuit(dag: DAGCircuit):
    """Build a ``QuantumCircuit`` object from a ``DAGCircuit``.

    Args:
        dag (DAGCircuit): the input dag.

    Return:
        QuantumCircuit: the circuit representing the input dag.
    """
    # In Qiskit, the quantum registers can have many diff names, whereas in PyZX circuit, there is only one global qubits.
    # We need a mapping from the global qubits back to the named qubits
    pyreg_range_to_qreg = dict()  # map the start idx of the named qreg to the name
    qreg_to_pyreg_range = dict()  # maps the qreg name to the start idx of global qreg
    tot_qb_count = 0

    qregs = OrderedDict()
    for qreg in dag.qregs.values():
        qreg_tmp = QuantumRegister(qreg.size, name=qreg.name)
        qregs[qreg.name] = qreg_tmp
        pyreg_range_to_qreg[tot_qb_count] = qreg.name
        qreg_to_pyreg_range[qreg.name] = tot_qb_count
        tot_qb_count += qreg.size

    cregs = OrderedDict()
    for creg in dag.cregs.values():
        creg_tmp = ClassicalRegister(creg.size, name=creg.name)
        cregs[creg.name] = creg_tmp

    name = dag.name or None
    gates = []

    for node in dag.topological_op_nodes():
        # collects the qregs
        qubits = [
            qreg_to_pyreg_range[qubit.register.name] + qubit.index
            for qubit in node.qargs
        ]

        # collects the cregs, which is passed (without conversion) to PyZX
        clbits = []
        for clbit in node.cargs:
            clbits.append(cregs[clbit.register.name][clbit.index])

        # if node.condition is not None:
        #     raise NotImplementedError(f"Classical control is not supported by PyZX")
        inst = node.op
        if check_classical_control(inst, qubits, gates,
                                   clbits=clbits, condition=node.condition):
            pass
        else:
            to_pyzx_gate(inst, qubits, gates,
                         clbits=clbits, condition=node.condition)

    circuit = Circuit(tot_qb_count, name='')
    circuit.gates = gates
    return circuit, qreg_to_pyreg_range, pyreg_range_to_qreg
