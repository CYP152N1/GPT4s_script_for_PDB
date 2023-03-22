import sys
import csv
import math
import argparse
from Bio import PDB
from Bio.PDB.Polypeptide import PPBuilder, three_to_one
from Bio.PDB.PDBExceptions import PDBConstructionWarning

class AltlocSelect(PDB.Select):
    def __init__(self, altloc):
        self.altloc = altloc

    def accept_atom(self, atom):
        return atom.altloc == self.altloc or atom.altloc == " "

def load_pdb_structure(pdb_file, altloc=None):
    parser = PDB.PDBParser(QUIET=True, PERMISSIVE=False)
    io = PDB.PDBIO()

    # Read the original PDB file
    original_structure = parser.get_structure("original_structure", pdb_file)

    if altloc is not None:
        # Filter the structure by altloc
        io.set_structure(original_structure)
        filtered_pdb_file = f"{pdb_file[:-4]}_filtered.pdb"
        io.save(filtered_pdb_file, AltlocSelect(altloc))

        # Read the filtered PDB file
        structure = parser.get_structure("structure", filtered_pdb_file)
    else:
        structure = original_structure

    return structure
def extract_dihedral_angles(structure, chain_id, altloc=None):
    if chain_id not in [chain.id for chain in structure[0]]:
        raise ValueError(f"Chain {chain_id} not found in PDB structure.")

    ppb = PPBuilder()
    torsion_angles = []

    for pp in ppb.build_peptides(structure[0][chain_id], aa_only=False):
        for i in range(len(pp) - 3):
            atoms = []
            valid_atoms = True
            
            for residue_index, atom_name in zip([i, i, i+1, i+1], ['O', 'C', 'N', 'H']):
                try:
                    residue = pp[residue_index]
                    atom = residue[atom_name]
                    if altloc is not None and altloc != "":
                        alt_atoms = [alt_atom for alt_atom in residue if alt_atom.name == atom_name and alt_atom.altloc != ""]
                        if alt_atoms:
                            valid_atoms = any(alt_atom.altloc == altloc for alt_atom in alt_atoms)
                            if valid_atoms:
                                atom = [alt_atom for alt_atom in alt_atoms if alt_atom.altloc == altloc][0]
                            else:
                                break
                        else:
                            valid_atoms = False
                            break
                    atoms.append(atom)
                except KeyError:
                    valid_atoms = False
                    break
            
            if not valid_atoms:
                print(f"Skipping residue pair {pp[i].get_resname()}({pp[i].get_id()[1]})-{pp[i+1].get_resname()}({pp[i+1].get_id()[1]}) due to missing or invalid atoms.")


            if valid_atoms and len(atoms) == 4:
                angle = PDB.calc_dihedral(*[atom.get_vector() for atom in atoms])
                angle_degrees = math.degrees(angle)
                res_id = pp[i+1].get_id()[1]
                res_name_i = pp[i].get_resname()
                res_name_i_plus_one = pp[i+1].get_resname()

                altloc_i = ""
                altloc_i_plus_one = ""

                if altloc is not None and altloc != "":
                    for atom in pp[i]:
                        if atom.name == "CA" and atom.altloc == altloc:
                            altloc_i = atom.altloc
                            break

                    for atom in pp[i+1]:
                        if atom.name == "CA" and atom.altloc == altloc:
                            altloc_i_plus_one = atom.altloc
                            break
                else:
                    altloc_i = pp[i]["CA"].altloc
                    altloc_i_plus_one = pp[i+1]["CA"].altloc

                if res_name_i in PDB.Polypeptide.aa3 and res_name_i_plus_one in PDB.Polypeptide.aa3:
                    res_name_i = f"{altloc_i}_{res_name_i}"
                    res_name_i_plus_one = f"{altloc_i_plus_one}_{res_name_i_plus_one}"
                    torsion_angles.append([res_name_i, res_name_i_plus_one, res_id, angle_degrees])

    return torsion_angles

def write_dihedral_angles_to_csv(torsion_angles_data, output_filename):
    with open(output_filename, "w", newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["Residue i", "Residue i+1", "Residue_ID", "O-C-N-H Dihedral Angle (degrees)"])
        for row in torsion_angles_data:
            csv_writer.writerow(row)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Calculate O-C-N-H dihedral angles in a PDB file.")
    parser.add_argument("pdb_file", help="Path to the PDB file.")
    parser.add_argument("chain_id", help="Chain ID to process.")
    parser.add_argument("-a", "--altloc", default=None, help="Alternate conformation ID (leave blank for default).")
    parser.add_argument("-o", "--output", default=None, help="Output CSV file name. If not specified, the output file will be named based on the input PDB file.")
    
    args = parser.parse_args()

    if args.altloc:
        output_filename = args.output or f"{args.pdb_file[:-4]}_{args.chain_id}_OCNH_dihedral_altloc_{args.altloc}.csv"
    else:
        output_filename = args.output or f"{args.pdb_file[:-4]}_{args.chain_id}_OCNH_dihedral.csv"
    
    try:
        structure = load_pdb_structure(args.pdb_file, args.altloc)  # 修正: args.altlocを渡します
        torsion_angles_data = extract_dihedral_angles(structure, args.chain_id, args.altloc)
        write_dihedral_angles_to_csv(torsion_angles_data, output_filename)
        print(f"O-C-N-H dihedral angles written to {output_filename}")
    except Exception as e:
        print(f"Error: {str(e)}")
