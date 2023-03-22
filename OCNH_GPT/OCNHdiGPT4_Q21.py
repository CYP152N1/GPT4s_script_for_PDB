import sys
import csv
import math
from Bio import PDB
from Bio.PDB.Polypeptide import PPBuilder, three_to_one
from Bio.PDB.PDBExceptions import PDBConstructionWarning

def load_pdb_structure(pdb_file):
    parser = PDB.PDBParser(QUIET=True, PERMISSIVE=False)
    structure = parser.get_structure("structure", pdb_file)
    return structure
def extract_dihedral_angles(structure, chain_id, altloc=None):
    if chain_id not in [chain.id for chain in structure[0]]:
        raise ValueError(f"Chain {chain_id} not found in PDB structure.")

    ppb = PPBuilder()
    torsion_angles = []

    for pp in ppb.build_peptides(structure[0][chain_id], aa_only=False):
        for i in range(len(pp) - 3):
            atoms = []
            for residue_index, atom_name in zip([i, i, i+1, i+1], ['O', 'C', 'N', 'H']):
                try:
                    residue = pp[residue_index]
                    atom = residue[atom_name]
                    if altloc is not None and altloc != "":
                        if atom.altloc not in (' ', altloc):
                            break
                        elif atom.altloc == altloc:
                            atoms.append(atom)
                            continue
                    else:
                        if atom.altloc != ' ':
                            continue
                    atoms.append(atom)
                except KeyError:
                    break

            if len(atoms) == 4:
                angle = PDB.calc_dihedral(*[atom.get_vector() for atom in atoms])
                angle_degrees = math.degrees(angle)
                res_id = pp[i+2].get_id()[1]
                res_name_i = pp[i].get_resname()
                res_name_i_plus_one = pp[i+1].get_resname()
                altloc_i = pp[i]["CA"].altloc
                altloc_i_plus_one = pp[i+1]["CA"].altloc

                if res_name_i in PDB.Polypeptide.aa3 and res_name_i_plus_one in PDB.Polypeptide.aa3:
                    res_name_i = f"{altloc_i}-{res_name_i}"
                    res_name_i_plus_one = f"{altloc_i_plus_one}-{res_name_i_plus_one}"
                    torsion_angles.append([res_name_i, res_name_i_plus_one, res_id, angle_degrees])

    return torsion_angles

def write_dihedral_angles_to_csv(torsion_angles_data, output_filename):
    with open(output_filename, "w", newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["Residue i", "Residue i+1", "Residue_ID", "O-C-N-H Dihedral Angle (degrees)"])
        for row in torsion_angles_data:
            csv_writer.writerow(row)

if __name__ == "__main__":
    pdb_file = input("Enter the path to your PDB file: ")
    chain_id = input("Enter chain ID: ")
    altloc = input("Enter alternate conformation ID (leave blank for default): ").strip() or None
    output_filename = f"{pdb_file[:-4]}_{chain_id}_OCNH_dihedral.csv"

    try:
        structure = load_pdb_structure(pdb_file)
        torsion_angles_data = extract_dihedral_angles(structure, chain_id, altloc)
        write_dihedral_angles_to_csv(torsion_angles_data, output_filename)
        print(f"O-C-N-H dihedral angles written to {output_filename}")
    except Exception as e:
        print(f"Error: {str(e)}")
                    
