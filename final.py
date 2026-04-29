import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import json

#Projection Constants (Written by me)
#NOTE: All dollar amounts are in billions
app_title        = "Federal Budget Allocation Model"
total_budget     = 7030   # Total 2025 Federal Budget in billions
simulation_years = 10     # Number of years to project forward
simulation_runs  = 500    # Number of Monte Carlo runs per projection
baseline_gdp = 30760.0 #Set baseline GDP at app launch. Number sourced from Federal Reserve 2025 estimate

# BUDGET CATEGORIES (Written by me)
# Each category has 5 fields:
#   baseline    - current 2025 spending in billions
#   min_pct     - minimum allowed % of total budget (reflects legal obligations)
#   max_pct     - maximum allowed % of total budget
#   color       - chart display color
#   description - plain English explanation shown in the GUI

budget_categories = {
    "Defense": {
        "baseline":    917,
        "min_pct":     2.0,
        "max_pct":     20.0,
        "color":       "#a9a9a9",
        "description": "Military personnel, weapons systems, homeland security, and VA benefits."
    },
    "Social Security": {
        "baseline":    1575,
        "min_pct":     18.0,
        "max_pct":     25.0,
        "color":       "#e6b800",
        "description": "Retirement and disability benefits for eligible Americans."
    },
    "Medicare": {
        "baseline":    1180,
        "min_pct":     12.0,
        "max_pct":     18.0,
        "color":       "#00008b",
        "description": "Federal health insurance for Americans 65+ and disabled individuals."
    },
    "Medicaid": {
        "baseline":    668,
        "min_pct":     8.0,
        "max_pct":     11.0,
        "color":       "#add8e6",
        "description": "Federal-state health coverage for low-income Americans."
    },
    "Education": {
        "baseline":    92,
        "min_pct":     1.0,
        "max_pct":     10.0,
        "color":       "#f57f17",
        "description": "K-12 Title I funding, Pell grants, student loans, vocational training."
    },
    "Infrastructure": {
        "baseline":    142,
        "min_pct":     1.0,
        "max_pct":     10.0,
        "color":       "#6a1b9a",
        "description": "Roads, bridges, rail, broadband, water systems, energy grid."
    },
    "R&D": {
        "baseline":    214,
        "min_pct":     2.0,
        "max_pct":     8.0,
        "color":       "#c62828",
        "description": "NIH, NASA, DARPA, NSF, clean energy research and development."
    },
    "Social Programs": {
        "baseline":    397,
        "min_pct":     4.0,
        "max_pct":     12.0,
        "color":       "#558b2f",
        "description": "SNAP, housing assistance, unemployment insurance, child care."
    },
    "Interest": {
        "baseline":    970,
        "min_pct":     8.0,
        "max_pct":     20.0,
        "color":       "#4e342e",
        "description": "Interest payments on national debt. Cannot be eliminated."
    },
    "Other": {
        "baseline":    845,
        "min_pct":     6.0,
        "max_pct":     15.0,
        "color":       "#546e7a",
        "description": "Foreign aid, federal courts, agriculture, energy, veterans programs."
    },
}

# FISCAL MULTIPLIERS (Written by me)
# Represents GDP dollars generated per dollar spent in each category
fiscal_multipliers = {
    "Defense":         0.95,
    "Social Security": 0.70,
    "Medicare":        0.60,
    "Medicaid":        0.90,
    "Education":       1.35,
    "Infrastructure":  1.85,
    "R&D":             1.60,
    "Social Programs": 1.20,
    "Interest":        0.00,  # No productive return — money leaves domestic economy
    "Other":           0.85,
}

# SOCIAL OUTCOME COEFFICIENTS (Written by me)
# Defines how much each social dimension improves or worsens based on spending changes in each category (values can be positive or negative)
# Each dimension starts at a neutral score of 50 out of 100
spending_return = {
    "Defense": {
        "National Security": 8.0,   # Primary purpose of defense spending
        "Economic Equality": -1.0,  # Defense contracts favor large corporations
        "Public Health":      0.5,
        "Education Index":    0.2,
        "Infrastructure":     0.3,
    },
    "Social Security": {
        "National Security":  0.0,
        "Economic Equality":  6.0,  # Directly reduces elder poverty
        "Public Health":      3.0,  # Financial stability improves health outcomes
        "Education Index":    0.5,
        "Infrastructure":     0.0,
    },
    "Medicare": {
        "National Security":  0.0,
        "Economic Equality":  4.0,
        "Public Health":      8.0,  # Direct healthcare access for seniors
        "Education Index":    0.5,
        "Infrastructure":     0.0,
    },
    "Medicaid": {
        "National Security":  0.0,
        "Economic Equality":  5.0,
        "Public Health":      7.0,  # Healthcare access for low-income Americans
        "Education Index":    1.0,
        "Infrastructure":     0.0,
    },
    "Education": {
        "National Security":  1.0,
        "Economic Equality":  7.0,  # Educated workforce reduces income inequality
        "Public Health":      2.0,
        "Education Index":   10.0,  # Direct investment in education system
        "Infrastructure":     0.5,
    },
    "Infrastructure": {
        "National Security":  2.0,
        "Economic Equality":  3.0,
        "Public Health":      2.0,
        "Education Index":    1.0,
        "Infrastructure":    10.0,  # Direct investment in physical systems
    },
    "R&D": {
        "National Security":  4.0,  # Military and dual-use technology
        "Economic Equality":  1.0,
        "Public Health":      3.0,  # Medical research breakthroughs
        "Education Index":    4.0,  # Advances academic and scientific knowledge
        "Infrastructure":     2.0,
    },
    "Social Programs": {
        "National Security":  0.0,
        "Economic Equality":  8.0,  # Direct assistance to lowest income Americans
        "Public Health":      4.0,
        "Education Index":    2.0,
        "Infrastructure":     0.0,
    },
    "Interest": {
        "National Security":  1.0,   # Maintaining credit rating has security value
        "Economic Equality": -2.0,   # Debt service crowds out social investment
        "Public Health":     -1.0,
        "Education Index":   -1.0,
        "Infrastructure":    -1.0,
    },
    "Other": {
        "National Security":  2.0,
        "Economic Equality":  1.0,
        "Public Health":      1.0,
        "Education Index":    1.0,
        "Infrastructure":     1.0,
    },
}

# GLOBAL STATE (Written by me, inspired by group project)
# Same pattern as M2 project — globals let screens share data without needing to pass variables between every function
saved_scenarios = []  # Stores up to 2 named scenarios for comparison
slider_vars = {}  # Holds tkinter DoubleVar objects for each slider
current_allocation = {}  # Most recent slider values converted to dollar amounts

# PROJECTION ENGINE (Written by me with AI consultation on Monte Carlo expansion from Group Project 2)
# Roughly a 75 me / 25 AI split in this section
def calculate_gdp_projection(allocation):
    # Runs 500 Monte Carlo simulations of the 10-year GDP projection to project real economic uncertainty

    all_runs = np.zeros((simulation_runs, simulation_years))  # Array to store all simulation results
    for run in range(simulation_runs):
        gdp = baseline_gdp

        for year in range(simulation_years):
            annual_delta = 0.0

            for category, dollars in allocation.items():
                multiplier = fiscal_multipliers[category]
                baseline_spend = budget_categories[category]["baseline"]
                delta_spend = dollars - baseline_spend  #Positive = spending increase, negative = spending cut

                annual_delta += (delta_spend * multiplier) / 10  # Divided by 10 because effect compounds over 10 years

            #2.1% baseline growth rate (10yr US GDP average)
            growth_rate = np.random.normal(0.021, 0.008)
            gdp = gdp + (gdp * growth_rate) + annual_delta
            all_runs[run, year] = round(gdp, 1)

    # Calculate summary statistics across all 500 runs — same as M2 project
    mean_path = np.mean(all_runs,  axis=0)
    p10_path  = np.percentile(all_runs, 10, axis=0)  # Bottom 10% outcome
    p90_path  = np.percentile(all_runs, 90, axis=0)  # Top 10% outcome

    return mean_path, p10_path, p90_path, all_runs


def calculate_social_scores(allocation): #This tertiary use of logic was inspired and written using the assistance of AI. Roughly AI 60 - 40 Me
    # Calculates a score for each social dimension based on how much each spending category was increased or decreased from baseline

    dimensions = ["National Security", "Economic Equality",
                  "Public Health", "Education Index", "Infrastructure"]

    scores = {d: 50.0 for d in dimensions}  #Every dimension starts neutral at 50. Info sourced from https://www.w3schools.com/python/python_dictionaries_comprehension.asp

    for category, dollars in allocation.items():
        baseline_spend = budget_categories[category]["baseline"]
        delta_100b     = (dollars - baseline_spend) / 100  #Convert to units of $100B to match coefficient scale

        for dimension in dimensions:
            coefficient       = spending_return[category][dimension]
            scores[dimension] += coefficient * delta_100b #Add weighted impact to dimension score

    for d in dimensions:
        scores[d] = round(max(0.0, min(100.0, scores[d])), 1) #Prevents scores from being negative or over 100. Clamping info sourced from https://www.geeksforgeeks.org/how-to-clamp-floating-point-values-in-python/

    return scores


def calculate_budget_grade(mean_path, social_scores): #This logic was thought of and written by Me
    #Generates a letter grade for the budget based on GDP growth AND social balance
    final_gdp      = mean_path[-1]
    gdp_growth_pct = ((final_gdp - baseline_gdp) / baseline_gdp) * 100 #Changes results into percentages

    # GDP grading portion of the simulation
    if gdp_growth_pct >= 25:
        gdp_points = 50
    elif gdp_growth_pct >= 20:
        gdp_points = 45
    elif gdp_growth_pct >= 15:
        gdp_points = 38
    elif gdp_growth_pct >= 10:
        gdp_points = 30
    elif gdp_growth_pct >= 5:
        gdp_points = 20
    else:
        gdp_points = 10

    #Social component worth up to 50 points (The first 3 lines were inspired by AI, the logic written by me)
    #Penalizes heavily if any single dimension is overly neglected
    avg_social    = sum(social_scores.values()) / len(social_scores)
    min_social    = min(social_scores.values())
    social_points = (avg_social / 100) * 50

    if min_social < 30:
        social_points -= 15  #Dangerous neglect such as cutting all healthcare
    elif min_social < 40:
        social_points -= 7   #Serious neglect

    total = round(gdp_points + social_points, 1)

    if total >= 80:
        grade, label = "A", "Exceptional Budget"
    elif total >= 68:
        grade, label = "B", "Strong Budget"
    elif total >= 55:
        grade, label = "C", "Adequate Budget"
    elif total >= 40:
        grade, label = "D", "Weak Budget"
    else:
        grade, label = "F", "Failing Budget"

    return grade, label, total


def get_allocation_from_sliders(): #Written by me
    # Reads current slider % values and converts each to dollar amount, logic inspired by Group Project 2
    allocation = {}
    for category, var in slider_vars.items():
        pct = var.get()
        allocation[category] = round((pct / 100) * total_budget, 1)
    return allocation


def get_baseline_allocation(): #Written by me
    # Calculates what % of total budget each category currently represents
    allocation = {}
    for category, data in budget_categories.items():
        allocation[category] = round((data["baseline"] / total_budget) * 100, 1)
    return allocation

#Clear window(s) #Written by me with pre-existing knowledge from other projects
def clear_window():
    for widget in root.winfo_children():
        widget.destroy()

#Welcome Screen #Written by me with pre-existing knowledge from other projects
def show_welcome():
    clear_window()
    root.title(app_title)

    tk.Label(root, text="Federal Budget Allocation Model",
             font=("Verdana", 28, "bold"), fg="#1a3c6e").pack(pady=(50, 5))
    tk.Label(root, text="Reallocate federal spending. See the 10-year economic and social impact.",
             font=("Verdana", 14, "italic"), fg="black").pack(pady=(0, 10))

    #Show constants like GDP baseline, Number of Simulations, and Total Budget on welcome screen
    stats_frame = tk.Frame(root, bg="#f0f4f8", relief="groove", bd=1)
    stats_frame.pack(padx=100, pady=15, fill="x")
    tk.Label(stats_frame,
             text=f"2025 Federal Budget: ${total_budget:,}B   |   GDP Baseline: ${baseline_gdp:,}B   |  {simulation_runs} Simulations",
             font=("Verdana", 12), bg="#f0f4f8", pady=10).pack()

    tk.Button(root, text="Build Your Budget", width=28, height=2,
              bg="#1a3c6e", fg="white", font=("Verdana", 14, "bold"),
              command=show_allocation_screen).pack(pady=10)

    tk.Button(root, text="Compare Saved Scenarios", width=28, height=2,
              bg="#2e7d32", fg="white", font=("Verdana", 12),
              command=show_comparison_screen).pack(pady=8)

    tk.Label(root, text=f"Scenarios saved this session: {len(saved_scenarios)}/2",
             font=("Verdana", 12), fg="black").pack(pady=(20, 0))

    tk.Label(root, text="Fiscal multiplier data sourced from CBO, IMF, and Brookings Institution.",
             font=("Verdana", 8), fg="black", wraplength=600).pack(pady=(5, 0))


def show_allocation_screen(): #First 2 lines as well as tklabels written by me with pre-existing knowledge from other projects
    clear_window()

    tk.Label(root, text="Build Your Budget",
             font=("Verdana", 24, "bold"), fg="#1a3c6e").pack(pady=(15, 2))
    tk.Label(root, text="Adjust spending sliders. Total must equal 100%. Run projection when ready.",
             font=("Verdana", 12, "italic"), fg="black").pack(pady=(0, 8))

    #Live running total updates every time a slider moves. Info sourced from https://www.pythontutorial.net/tkinter/tkinter-stringvar/
    total_var   = tk.StringVar()
    total_label = tk.Label(root, textvariable=total_var, font=("Verdana", 11, "bold"))
    total_label.pack(pady=(0, 8))

    #Scroll bar for small window sourced from https://www.geeksforgeeks.org/scrollable-frames-in-tkinter/
    canvas_frame = tk.Frame(root)
    canvas_frame.pack(fill="both", expand=True, padx=30)
    canvas   = tk.Canvas(canvas_frame)
    scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
    scroll_frame = tk.Frame(canvas)

    scroll_frame.bind("<Configure>",
                      lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

    canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    baseline_pcts = get_baseline_allocation()  #Load 2025 percentages for slider starting positions. Leaves 0.6% unassigned as some metrics are conflicting + misc sources exist

    def update_total(*args): #Recalculates running total every time any slider moves
        #Following 2 lines sourced from https://www.w3schools.com/python/python_generators.asp
        total     = round(sum(v.get() for v in slider_vars.values()), 1)
        remaining = round(100.0 - total, 1)

        if abs(remaining) < 0.1: #This logic was written by me using basic knolwedge of if statements and colors.
            total_var.set(f"Total Allocated: {total}%. Ready to run!")
            total_label.config(fg="#1a6e1a")  #Green when spending is exactly 100%
        elif remaining > 0:
            total_var.set(f"Total Allocated: {total}%. {remaining}% remaining")
            total_label.config(fg="#8b6914")  #Yellow when spending is under 100%
        else:
            total_var.set(f"Total Allocated: {total}%.  {abs(remaining)}% over budget!")
            total_label.config(fg="#8b1a1a")  #Red when spending is over 100%

    #Build one row per category. Info sourced from https://www.geeksforgeeks.org/python/python-gui-tkinter/
    for i, (category, data) in enumerate(budget_categories.items()): #creats a slider for each cateogry
        row = tk.Frame(scroll_frame, pady=4) #builds frame for slider
        row.pack(fill="x", padx=10) #positions slider

        tk.Label(row, text=category, font=("Verdana", 10, "bold"), #This button and next button written by me.
                 width=16, anchor="w", fg=data["color"]).pack(side="left")
        tk.Label(row, text=data["description"], font=("Verdana", 8),
                 fg="black", width=52, anchor="w").pack(side="left")

        #Code to start at 2025 baseline sourced from https://www.pythontutorial.net/tkinter/tkinter-trace-variable/
        var = tk.DoubleVar(value=baseline_pcts[category])
        var.trace("w", update_total)
        slider_vars[category] = var

        #Label creation. Written by me with prior knowledge
        pct_label = tk.Label(row, font=("Verdana", 12, "bold"), width=6)
        pct_label.pack(side="right")
        dollar_label = tk.Label(row, font=("Verdana", 8), fg="black", width=10)
        dollar_label.pack(side="right")

        def make_update(v=var, pl=pct_label, dl=dollar_label): #This section was roughly a 50/50 split between AI and sources https://www.geeksforgeeks.org/python-closures/ and https://www.pythontutorial.net/tkinter/tkinter-scale/
            #Keeps slider labels updating independently
            def update(*args):
                pct     = round(v.get(), 1)
                dollars = round((pct / 100) * total_budget, 1)
                pl.config(text=f"{pct}%")
                dl.config(text=f"${dollars:,}B")
            return update

        updater = make_update()
        var.trace("w", lambda *args, u=updater: u())
        updater()  #Run so labels populate immediately

        tk.Scale(row, variable=var,
                 from_=data["min_pct"], to=data["max_pct"],
                 resolution=0.1, orient="horizontal",
                 length=220, showvalue=False,
                 troughcolor=data["color"]).pack(side="left", padx=8)

    update_total()

    btn_frame = tk.Frame(root) #Written by me using previous knowledge
    btn_frame.pack(pady=10) #Written by me using previous knowledge

    tk.Button(btn_frame, text="Run Projection", width=20, height=2, #Button written by me using previous knowledge
              bg="#1a3c6e", fg="white", font=("Verdana", 11, "bold"),
              command=run_projection).pack(side="left", padx=8)

    tk.Button(btn_frame, text="Reset to Baseline", width=20, height=2,  #Button written by me using previous knowledge
              bg="#555", fg="white", font=("Verdana", 11),
              command=reset_to_baseline).pack(side="left", padx=8)

    tk.Button(btn_frame, text="Home", width=12, height=2,  #Button written by me using previous knowledge
              bg="lightgray", font=("Verdana", 11),
              command=show_welcome).pack(side="left", padx=8)


def reset_to_baseline(): #.set method sourced from https://www.pythontutorial.net/tkinter/tkinter-trace-variable/, rest written be me
    #Resets sliders back to real 2025 percentages
    baseline_pcts = get_baseline_allocation()
    for category, var in slider_vars.items():
        var.set(baseline_pcts[category])


def run_projection(): #Validates budget equals 100% then runs all three model functions inspired from Group Project. Roughly 75/25 split between me and AI
    total = round(sum(v.get() for v in slider_vars.values()), 1)
    if abs(total - 100.0) > 0.5:
        messagebox.showerror("Budget Error",
                             f"Total allocation is {total}%. Must equal 100% before running.")
        return

    allocation = get_allocation_from_sliders()
    mean_path, p10, p90, all_runs = calculate_gdp_projection(allocation)
    scores = calculate_social_scores(allocation)
    grade, label, total_score = calculate_budget_grade(mean_path, scores)

    global current_allocation
    current_allocation = allocation  #Storage for save/compare features

    show_results_screen(allocation, mean_path, p10, p90, all_runs, scores, grade, label, total_score)


def show_results_screen(allocation, mean_path, p10, p90, all_runs, scores, grade, label, total_score): #This section was a mix of me, AI, and sources, so I will go by subsection.
    clear_window() #Written by me

    grade_colors = {"A": "#1a6e1a", "B": "#2e7d9e", "C": "#8b6914", #These 3 lines written by me
                    "D": "#8b4500", "F": "#8b1a1a"}
    grade_color  = grade_colors.get(grade, "#333")

    tk.Label(root, text="Projection Results", #Label written by me
             font=("Verdana", 20, "bold"), fg="#1a3c6e").pack(pady=(15, 2))

    #These 2 grade banner lines written by me + information sourced from https://www.geeksforgeeks.org/python/python-gui-tkinter/
    header_frame = tk.Frame(root, bg="#f0f4f8", relief="groove", bd=1)
    header_frame.pack(padx=30, fill="x", pady=(0, 8))

    tk.Label(header_frame, #This small section written by me + AI
             text=f"Budget Grade: {grade}  —  {label}  ({total_score}/100)",
             font=("Verdana", 14, "bold"), fg=grade_color,
             bg="#f0f4f8", pady=8).pack(side="left", padx=20)

    final_gdp  = mean_path[-1] #These two lines written by me. This line grabs 10 year GDP prediction from simulation
    gdp_growth = ((final_gdp - baseline_gdp) / baseline_gdp) * 100 #Calculates % growth over 10 year period
    tk.Label(header_frame, #These two lines written by me with small help from AI. Roughly 80-20 split
             text=f"Projected GDP Year 10: ${final_gdp:,.0f}B  |  Growth: {gdp_growth:.1f}%  |  Based on {simulation_runs} simulations",
             font=("Verdana", 10), bg="#f0f4f8", pady=8).pack(side="left", padx=10)

    #Embeds results chart written using info sourced from https://matplotlib.org/stable/gallery/user_interfaces/embedding_in_tk_sgskip.html
    fig    = build_results_chart(mean_path, p10, p90, all_runs, scores)
    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=(0, 5))

    btn_frame = tk.Frame(root) #Used information sourced from https://www.geeksforgeeks.org/python/python-gui-tkinter/
    btn_frame.pack(pady=8)

    tk.Button(btn_frame, text= "Save Scenario", width=18, height=2, #Button written by me
              bg="#2e7d32", fg="white", font=("Verdana", 12),
              command=lambda: save_scenario(allocation, mean_path, p10, p90, #Saves current scenario to allow comparisons
                                            scores, grade, label, total_score)
              ).pack(side="left", padx=8)

    tk.Button(btn_frame, text="Adjust Budget", width=18, height=2, #Button written by me
              bg="#1a3c6e", fg="white", font=("Verdana", 12),
              command=show_allocation_screen).pack(side="left", padx=8)

    tk.Button(btn_frame, text="Compare Scenarios", width=18, height=2, #Button written by me
              bg="#555", fg="white", font=("Verdana", 12),
              command=show_comparison_screen).pack(side="left", padx=8) #Button written by me

    tk.Button(btn_frame, text="Home", width=12, height=2, #Button written by me
              bg="lightgray", font=("Verdana", 12),
              command=show_welcome).pack(side="left", padx=8)


def build_results_chart(mean_path, p10, p90, all_runs, scores): #Written by me inspired by Group Project + other knowledge
    #Two plots shown with GDP Monte Carlo projection left, social scores right
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
    years = list(range(1, simulation_years + 1))

    #GDP Monte Carlo Projection written using info sourced from https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.plot.html
    for i in range(0, simulation_runs, 10):
        ax1.plot(years, all_runs[i], color="lightblue", alpha=0.15, linewidth=0.5)

    #Baseline/no change path for comparison. This subsection written by me using info from https://www.w3schools.com/python/python_lists_comprehension.asp
    baseline_path = [baseline_gdp * ((1.021) ** y) for y in years]
    ax1.plot(years, baseline_path, color="gray", linewidth=1.5,
             linestyle="--", label="Baseline (No Change)", zorder=3) #This line written by me alone

    #Mean projection and percentile bands. Sources for this section are https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.fill_between.html and https://matplotlib.org/stable/api/ticker_api.html, as well as some inspiration from Group Project
    ax1.plot(years, mean_path, color="#1a3c6e", linewidth=2.5,
             label="Mean Projection", zorder=4, marker="o", markersize=3) #Plots mean GDP line
    ax1.fill_between(years, p10, p90, alpha=0.2,
                     color="#1a3c6e", label="10th–90th Percentile") #Creates shaded region of 10th and 90th percentiles

    ax1.set_title(f"10-Year GDP Projection ({simulation_runs} Simulations)",
                  fontsize=11, fontweight="bold")
    ax1.set_xlabel("Year", fontsize=10)
    ax1.set_ylabel("GDP (Billions $)", fontsize=10)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda val, _: f"${val:,.0f}B")) #labels y-axis as dollar amounts
    ax1.legend(fontsize=8, loc="upper left")
    ax1.grid(axis="y", alpha=0.3)

    #Social Scores Bar Chart #Written and logically developed by me, structurally uses info sourced from https://www.w3schools.com/python/python_lists_comprehension.asp
    dimensions = list(scores.keys())
    values     = list(scores.values())
    colors     = ["#1a6e1a" if v >= 60 else "#8b6914"
                  if v >= 40 else "#8b1a1a" for v in values]  #Green/gold/red by score level

    bars = ax2.barh(dimensions, values, color=colors, edgecolor="white", height=0.5) #These few lines use info sourced from https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.barh.html
    for bar, val in zip(bars, values):
        ax2.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                 f"{val}", va="center", fontsize=9, fontweight="bold")

    ax2.axvline(x=50, color="gray", linestyle="--", linewidth=1, #The rest of the graphing lines written use knowledge from this projects and others
                alpha=0.7, label="Neutral (50)")
    ax2.set_xlim(0, 115)
    ax2.set_title("Social Outcome Scores", fontsize=11, fontweight="bold")
    ax2.set_xlabel("Score (0–100)", fontsize=10)
    ax2.legend(fontsize=8)

    fig.tight_layout()
    return fig

def save_scenario(allocation, mean_path, p10, p90, scores, grade, label, total_score): #Written by me using knolwedge acquired from other projects
    #Saves current results to saved_scenarios list
    if len(saved_scenarios) >= 2:
        messagebox.showwarning("Limit Reached",
                               "You already have 2 saved scenarios."
                               "Go to Compare Scenarios to view or clear them.")
        return

    #Popup asks user to name their scenario before saving. TopLevel logic sourced from sourced from https://www.pythontutorial.net/tkinter/tkinter-toplevel/, coding and naming done by me
    name_window = tk.Toplevel(root)
    name_window.title("Name Your Scenario")
    name_window.geometry("340x140")
    name_window.grab_set()  #Blocks main window until closed

    tk.Label(name_window, text="Enter a name for this scenario:", #Top 2 lines written be me
             font=("Verdana", 12)).pack(pady=(20, 8))
    name_entry = tk.Entry(name_window, font=("Verdana", 12), width=24) #Info for these 3 lines sourced from Group Project
    name_entry.pack()
    name_entry.insert(0, f"Scenario {len(saved_scenarios) + 1}")

    def confirm(): #Consulted AI on this section. 70% done by AI
        name = name_entry.get().strip() or f"Scenario {len(saved_scenarios) + 1}"
        saved_scenarios.append({
            "name":        name,
            "allocation":  allocation,
            "mean_path":   mean_path.tolist(),  #Converts numpy data to list for JSON
            "p10":         p10.tolist(),
            "p90":         p90.tolist(),
            "scores":      scores,
            "grade":       grade,
            "label":       label,
            "total_score": total_score
        })
        name_window.destroy() #closes popup window after saving
        messagebox.showinfo("Saved",
                            f'"{name}" saved. {2 - len(saved_scenarios)} slot(s) remaining.')

    tk.Button(name_window, text="Save", width=14, #Button written by me
              bg="#2e7d32", fg="white", font=("Verdana", 12),
              command=confirm).pack(pady=12)


def show_comparison_screen(): #These two lines written by me. Overall section is 90% me, 10% AI just for structural purposes.
    clear_window()

    tk.Label(root, text="Scenario Comparison", #Label written by me
             font=("Verdana", 20, "bold"), fg="#1a3c6e").pack(pady=(20, 5))

    if len(saved_scenarios) < 2:
        #Not enough saved so guides user back to build a budget
        tk.Label(root, #Written by me
                 text=f"You need 2 saved scenarios to compare. Currently saved: {len(saved_scenarios)}/2",
                 font=("Verdana", 12), fg="black", justify="center").pack(pady=40)

        tk.Button(root, text="Go Build a Budget", width=22, height=2, #Written by me
                  bg="#1a3c6e", fg="white", font=("Verdana", 12),
                  command=show_allocation_screen).pack(pady=10)

        if saved_scenarios: #Written by me
            tk.Button(root, text="Clear Saved Scenarios", width=22,
                      bg="#8b1a1a", fg="white", font=("Verdana", 12),
                      command=clear_scenarios).pack(pady=5)
        return

    s1, s2 = saved_scenarios[0], saved_scenarios[1] #Calls both saved scenarios to allow comparisons

    #Compares grade summaries. Written by me from previous projects
    summary_frame = tk.Frame(root)
    summary_frame.pack(padx=30, fill="x", pady=(0, 8))

    grade_colors = {"A": "#1a6e1a", "B": "#2e7d9e", "C": "#8b6914", #previously written by me
                    "D": "#8b4500", "F": "#8b1a1a"}

    for s, side in [(s1, "left"), (s2, "right")]: #Uses info sourced from https://www.geeksforgeeks.org/python/python-gui-tkinter/
        f = tk.Frame(summary_frame, relief="groove", bd=2, padx=10, pady=8) #Creates frame for each scenario
        f.pack(side=side, expand=True, fill="x", padx=10)
        tk.Label(f, text=s["name"],
                 font=("Verdana", 12, "bold")).pack() #Displays Scenario Name
        tk.Label(f, text=f"{s['grade']} — {s['label']}",
                 font=("Verdana", 12, "bold"),
                 fg=grade_colors.get(s["grade"], "#333")).pack() #Displays grade
        tk.Label(f, text=f"Score: {s['total_score']}/100",
                 font=("Verdana", 12), fg="black").pack() #Displays numerical grade
        final_gdp = s["mean_path"][-1] #Grabs 10 year final GDP
        gdp_growth = ((final_gdp - baseline_gdp) / baseline_gdp) * 100 #calculates growth %
        tk.Label(f, text=f"Year 10 GDP: ${final_gdp:,.0f}B  ({gdp_growth:.1f}% growth)",
                 font=("Verdana", 12)).pack()

    #Comparison chart. This section written using Group Project 2 knowledge and info sourced from https://matplotlib.org/stable/gallery/user_interfaces/embedding_in_tk_sgskip.html
    fig = build_comparison_chart(s1, s2) #Creates chart
    canvas = FigureCanvasTkAgg(fig, master=root) #Creates Tkinter GUI from chart
    canvas.draw() #Draws chart
    canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=(0, 5)) #positions chart

    btn_frame = tk.Frame(root) #Written by me from previous knowledge
    btn_frame.pack(pady=8)

    tk.Button(btn_frame, text="Clear & Start Over", width=20, height=2, #Written by me from previous knowledge
              bg="#8b1a1a", fg="white", font=("Verdana", 11),
              command=clear_scenarios).pack(side="left", padx=8)

    tk.Button(btn_frame, text="Build Another Budget", width=20, height=2, #Written by me from previous knowledge
              bg="#1a3c6e", fg="white", font=("Verdana", 11),
              command=show_allocation_screen).pack(side="left", padx=8)

    tk.Button(btn_frame, text="Home", width=12, height=2, #Written by me from previous knowledge
              bg="lightgray", font=("Verdana", 11),
              command=show_welcome).pack(side="left", padx=8)


def build_comparison_chart(s1, s2): #Three charts: GDP comparison, social scores comparison, spending difference.
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(13, 4)) #creates the three charts
    years = list(range(1, simulation_years + 1))

    #GDP Mean Path Comparison. Written by me using info sourced from https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.subplots.html
    ax1.plot(years, s1["mean_path"], color="#1a3c6e", linewidth=2.5,
             label=s1["name"], marker="o", markersize=3) #Plots Mean GDP line for scenario 1
    ax1.fill_between(years, s1["p10"], s1["p90"], alpha=0.1, color="#1a3c6e") #Creates shaded area in Scenario 1

    ax1.plot(years, s2["mean_path"], color="#c62828", linewidth=2.5,
             label=s2["name"], marker="s", markersize=3) #Plots Mean GDP line for scenario 2
    ax1.fill_between(years, s2["p10"], s2["p90"], alpha=0.1, color="#c62828") #Creates shaded area in Scenario 1

    ax1.set_title("GDP Projection Comparison", fontsize=12, fontweight="bold") #Chart title/font
    ax1.set_xlabel("Year", fontsize=8) #X Axis Label
    ax1.set_ylabel("GDP (Billions $)", fontsize=8) #Y Axis Label
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda val, _: f"${val:,.0f}B"))
    ax1.legend(fontsize=8)
    ax1.grid(axis="y", alpha=0.3)

    #Social Score Comparison
    dimensions = list(s1["scores"].keys())
    s1_vals = list(s1["scores"].values()) #Gets scenario 1 social scores
    s2_vals = list(s2["scores"].values()) #GEts scenario 2 social scores
    x = np.arange(len(dimensions)) #spaces bars on x axis evenly
    width = 0.35 #defines each bars width

    #Grouped bar chart sourced from https://matplotlib.org/stable/api/_as_gen/matplotlib.axes.Axes.bar.html
    ax2.bar(x - width/2, s1_vals, width, label=s1["name"], color="#1a3c6e", alpha=0.85) #Shifts scenario 1 bars
    ax2.bar(x + width/2, s2_vals, width, label=s2["name"], color="#c62828", alpha=0.85) #Shifts scenario 2 bars
    ax2.axhline(y=50, color="gray", linestyle="--", linewidth=1, alpha=0.7) #Draws baseline at 50
    ax2.set_title("Social Outcomes", fontsize=11, fontweight="bold")
    ax2.set_xticks(x)
    ax2.set_xticklabels([d.replace(" ", "\n") for d in dimensions], fontsize=8) #Splits label into two lines to make it fit
    ax2.set_ylim(0, 110) #sets y axis limit
    ax2.legend(fontsize=8)

    #Spending Difference (Written by Me using information from https://www.w3schools.com/python/python_lists_comprehension.asp
    categories = list(s1["allocation"].keys()) #gets category names
    diffs = [s2["allocation"][c] - s1["allocation"][c] for c in categories] #Caclulates difference in categories between scenarios
    diff_colors = ["#1a6e1a" if d > 0 else "#8b1a1a" for d in diffs]  #Green = S2 spent more, Red = S2 spent less per category

    ax3.barh(categories, diffs, color=diff_colors, edgecolor="white") #Horizontal bars showing spending differences
    ax3.axvline(x=0, color="black", linewidth=0.8) #Vertical line at 0
    ax3.set_title(f"{s2['name']} vs {s1['name']}\nSpending Difference ($B)", #Title for named scenarios being compared
                  fontsize=10, fontweight="bold")
    ax3.set_xlabel("Difference ($B)", fontsize=8)

    fig.tight_layout() #Aligns 3 charts
    return fig #Returns all 3 charts to tkinter window

def clear_scenarios(): #Wipes both saved scenarios and returns to welcome screen #Written by me
    global saved_scenarios
    saved_scenarios = []
    messagebox.showinfo("Cleared", "Saved scenarios have been cleared.")
    show_welcome()

#Application Loop (Written by me)
root = tk.Tk()
root.title(app_title)
root.geometry("900x700")
show_welcome()
root.mainloop()