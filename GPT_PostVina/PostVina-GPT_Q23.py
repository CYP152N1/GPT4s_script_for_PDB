import sys
import csv
import re
import math
import argparse

def parse_pdb(file_path):
    with open(file_path, 'r') as f:
        pdb_lines = f.readlines()

    data_matrix = []

    for line in pdb_lines:
        if line.startswith("ATOM"):
            atom_label = line[12:16].strip()
            if atom_label not in ["C", "N", "O", "CA"]:
                residue_name = line[17:20].strip()
                residue_number = int(line[22:26].strip())
                x = float(line[30:38].strip())
                y = float(line[38:46].strip())
                z = float(line[46:54].strip())

                data_matrix.append([atom_label, residue_name, residue_number, x, y, z])

    return data_matrix

def parse_pdbqt(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()

    models = []
    current_model = []

    for line in lines:
        if line.startswith('MODEL'):
            current_model = []
        elif line.startswith('ATOM') or line.startswith('HETATM'):
            atom_label = line[12:16].strip()
            x = float(line[30:38].strip())
            y = float(line[38:46].strip())
            z = float(line[46:54].strip())
            current_model.append((atom_label, x, y, z))
        elif line.startswith('ENDMDL'):
            models.append(current_model)

    return models

def distance(coord1, coord2):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(coord1, coord2)))

def find_nearby_residues(pdb_data, pdbqt_models, threshold=5.0):
    nearby_residues_list = []

    for model_index, model in enumerate(pdbqt_models, start=1):  # 追加: インデックスを1から開始
        nearby_residues = set()
        for atom_pdbqt in model:
            for atom_pdb in pdb_data:
                if atom_pdb[0] not in ["C", "N", "O", "CA"]:
                    dist = distance(atom_pdb[3:6], atom_pdbqt[1:4])
                    if dist <= threshold:
                        # model_indexを使ってモデル番号を記録
                        nearby_residues.add((atom_pdb[0], atom_pdb[1], atom_pdb[2], model_index, atom_pdbqt[0]))
        nearby_residues_list.append(nearby_residues)

    return nearby_residues_list


def main(args):
    pdb_file = args.pdb_file
    pdbqt_file = args.pdbqt_file
    output_csv = args.output_csv
    threshold = args.threshold  # 追加

    pdb_data = parse_pdb(pdb_file)
    pdbqt_models = parse_pdbqt(pdbqt_file)

    nearby_residues_list = find_nearby_residues(pdb_data, pdbqt_models, threshold)  # thresholdを渡す

    with open(output_csv, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['PDB_Atom', 'Residue_Name', 'Residue_Number', 'PDBQT_Model', 'PDBQT_Atom'])

        for i, nearby_residues in enumerate(nearby_residues_list):
            for pdb_label, residue_name, residue_number, model_number, atom_label in nearby_residues:
                csv_writer.writerow([pdb_label, residue_name, residue_number, model_number, atom_label])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Find nearby residues in PDBQT models")
    parser.add_argument("pdb_file", type=str, help="Input PDB file")
    parser.add_argument("pdbqt_file", type=str, help="Input PDBQT file")
    parser.add_argument("output_csv", type=str, help="Output CSV file")
    parser.add_argument("-t", "--threshold", type=float, default=5.0, help="Distance threshold for nearby residues (default: 5.0)")

    args = parser.parse_args()
    main(args)
