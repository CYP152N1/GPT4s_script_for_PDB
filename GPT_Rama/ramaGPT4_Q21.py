import sys
import csv
import math
import os
from Bio import PDB
from Bio.PDB.Polypeptide import PPBuilder, protein_letters_3to1
from Bio.PDB.PDBExceptions import PDBConstructionWarning
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from io import StringIO
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def fetch_pdb(pdb_id):
    pdb_list = PDB.PDBList()
    filename = pdb_list.retrieve_pdb_file(pdb_id, pdir=".")
    return filename

    phi_psi_data = extract_phi_psi(pdb_id, chain_id, structure)
    write_to_csv(phi_psi_data, csv_output)
    
    csv_text.delete('1.0', tk.END)
    csv_output_str = csv_output.getvalue().replace('\r\n', '\n').replace('\r', '\n')
    csv_text.insert(tk.END, csv_output_str)
    
    plot_scatter(phi_psi_data)

def extract_phi_psi(pdb_id, chain_id, filename):
    file_format = os.path.splitext(filename)[1]
    if file_format == ".ent":
        parser = PDB.PDBParser(QUIET=True, PERMISSIVE=False)
    elif file_format == ".cif":
        parser = PDB.MMCIFParser(QUIET=True)
    else:
        raise ValueError("Invalid file format. Use either '.ent' (PDB) or '.cif' (mmCIF).")

    structure = parser.get_structure(pdb_id, filename)

    if chain_id not in [chain.id for chain in structure[0]]:
        raise ValueError(f"Chain {chain_id} not found in PDB structure.")

    ppb = PPBuilder()
    phi_psi = []

    for pp in ppb.build_peptides(structure[0][chain_id], aa_only=False):
        for residue, angles in zip(pp, pp.get_phi_psi_list()):
            res_name = residue.get_resname().upper()
            res_id = residue.get_id()[1]

            if res_name in PDB.Polypeptide.aa3:
                res_name_1 = protein_letters_3to1[res_name]
                phi, psi = angles

                if phi and psi:
                    phi_degrees = math.degrees(phi)
                    psi_degrees = math.degrees(psi)
                    phi_psi.append([res_name_1, res_id, phi_degrees, psi_degrees])

    return phi_psi

def write_to_csv(phi_psi_data, csv_output):
    csv_writer = csv.writer(csv_output)
    csv_writer.writerow(["Residue", "Residue_ID", "Phi (degrees)", "Psi (degrees)"])

    for residue_data in phi_psi_data:
        residue_name = residue_data[0]
        residue_id = residue_data[1]
        phi = round(residue_data[2], 2)  # 丸める
        psi = round(residue_data[3], 2)  # 丸める
        csv_writer.writerow([residue_name, residue_id, phi, psi])

def run_analysis():
    pdb_id = pdb_id_entry.get()
    chain_id = chain_id_entry.get()

    try:
        filename = fetch_pdb(pdb_id)
        phi_psi_data = extract_phi_psi(pdb_id, chain_id, filename)

        pdb_text.delete('1.0', tk.END)
        with open(filename, "r") as f:
            pdb_text.insert(tk.END, f.read())

        csv_output = StringIO()
        csv_writer = csv.writer(csv_output)
        csv_writer.writerow(["Residue", "Residue_ID", "Phi (degrees)", "Psi (degrees)"])
        for row in phi_psi_data:
            csv_writer.writerow(row)

        csv_text.delete('1.0', tk.END)
        csv_output_str = csv_output.getvalue().replace('\r\n', '\n').replace('\r', '\n')
        csv_text.insert(tk.END, csv_output_str)

    except Exception as e:
        error_label.config(text=f"Error: {str(e)}")

def save_csv():
    pdb_id = pdb_id_entry.get()
    chain_id = chain_id_entry.get()
    default_filename = f"{pdb_id}_{chain_id}.csv"
    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv")], initialfile=default_filename)
    if file_path:
        with open(file_path, "w") as f:
            f.write(csv_text.get("1.0", tk.END))

def plot_scatter(phi_psi_data):
    phi = [round(data[2], 2) for data in phi_psi_data]
    psi = [round(data[3], 2) for data in phi_psi_data]
    
    plt.scatter(phi, psi)
    plt.xlabel('Phi (degrees)')
    plt.ylabel('Psi (degrees)')
    plt.title('Phi-Psi Scatter Plot')
    plt.show()

def plot_scatter(phi_psi_data):
    fig, ax = plt.subplots()
    phi = [round(data[2], 2) for data in phi_psi_data]
    psi = [round(data[3], 2) for data in phi_psi_data]
    
    ax.scatter(phi, psi)
    ax.set_xlabel('Phi (degrees)')
    ax.set_ylabel('Psi (degrees)')
    ax.set_title('Phi-Psi Scatter Plot')

    return fig

def show_scatter():
    pdb_id = pdb_id_entry.get()
    chain_id = chain_id_entry.get()
    filename = fetch_pdb(pdb_id)  # filename を取得

    phi_psi_data = extract_phi_psi(pdb_id, chain_id, filename)  # filename を渡す
    fig = plot_scatter(phi_psi_data)
    
    scatter_canvas = FigureCanvasTkAgg(fig, master=app)
    scatter_canvas.draw()
    scatter_canvas.get_tk_widget().grid(row=1, column=3, rowspan=2, padx=10, pady=10, sticky="nsew")

app = tk.Tk()
app.title("PDB Phi-Psi Analyzer")

frame = ttk.Frame(app, padding="10")
frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))

pdb_id_label = ttk.Label(frame, text="PDB ID:")
pdb_id_label.grid(row=0, column=0, sticky=tk.W)
pdb_id_entry = ttk.Entry(frame, width=10)
pdb_id_entry.grid(row=0, column=1, sticky=tk.W)

chain_id_label = ttk.Label(frame, text="Chain ID:")
chain_id_label.grid(row=1, column=0, sticky=tk.W)
chain_id_entry = ttk.Entry(frame, width=10)
chain_id_entry.grid(row=1, column=1, sticky=tk.W)

analyze_button = ttk.Button(frame, text="Analyze", command=run_analysis)
analyze_button.grid(row=2, column=0, columnspan=2, pady=10)

pdb_text = tk.Text(app, wrap=tk.NONE, width=80, height=20)
pdb_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

pdb_scroll = ttk.Scrollbar(app, orient="vertical", command=pdb_text.yview)
pdb_scroll.grid(row=1, column=1, sticky=(tk.N, tk.S))
pdb_text.config(yscrollcommand=pdb_scroll.set)

csv_text = tk.Text(app, wrap=tk.NONE, width=80, height=20)
csv_text.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.N, tk.S))

csv_scroll = ttk.Scrollbar(app, orient="vertical", command=csv_text.yview)
csv_scroll.grid(row=1, column=3, sticky=(tk.N, tk.S))
csv_text.config(yscrollcommand=csv_scroll.set)

error_label = ttk.Label(app, text="", foreground="red")
error_label.grid(row=2, column=0, columnspan=2, pady=10)

save_button = ttk.Button(app, text="Save CSV", command=save_csv)
save_button.grid(row=2, column=1, pady=10)

scatter_button = ttk.Button(app, text="Show Scatter Plot", command=show_scatter)
scatter_button.grid(row=2, column=3, padx=(0, 10), pady=10)

app.columnconfigure(0, weight=1)
app.columnconfigure(1, weight=0)
app.columnconfigure(2, weight=1)
app.columnconfigure(3, weight=0)
app.rowconfigure(1, weight=1)

app.mainloop()
