from pathlib import Path
from textwrap import fill
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter


def analyze_lab_disposables(df_unclean, output_dir="./results"):
    """
    Filter laboratory disposables, create impact tables and visualizations, and save the results
    - df_unclean = dataframe containing the full product dataset
    - output_dir = folder where tables and visualizations will be saved
    """

    #create the output folder for tables and visualizations
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    #keep only products marked for inclusion
    df = df_unclean[df_unclean["is_included"] == True].copy()

    #exclude glass bottles from the analysis
    mask = ~(
        (df["categorie"] == "Bottles") &
        (df["materialen"].str.contains("glass", case=False, na=False))
    )
    df = df[mask]

    #exclude reusable product categories from the analysis
    df = df[
        ~df["categorie"].isin(
            ["Volumetric Labware", "Forceps (Reusable)", "Spatulas (Reusable)"]
        )
    ]

    df["gewicht_totaal_kg"] = ((df["gewicht_per_stuk"] * df["stuks_totaal"]) / 1000)
    
    #map English category names to Dutch category names
    label_mapping = {
        "Serological Pipettes": "Serologische pipetten",
        "Centrifuge Tubes": "Centrifugebuizen",
        "Multiwell Plates": "Multiwell platen",
        "Blood Collection Tubes": "Bloedbuizen",
        "Cell Culture Flasks": "Celkweek flessen",
        "Petri Dishes": "Petrischalen",
        "N-Filter Pipette Tips": "Pipetpunten zonder filter",
        "Gloves": "Handschoenen",
        "Test Tubes": "Reageerbuizen",
        "Microtubes": "Microbuizen",
        "Filter Pipette Tips": "Pipetpunten met filter",
        "Grip and Safety Bags": "Gripzakjes en safetybags",
        "Containers and Cups": "Containers en cups",
        "Microscope Slides": "Objectglaasjes",
        "Syringes": "Spuiten",
        "Pasteur Pipettes": "Pasteur pipetten",
        "Plate Sealing Foils": "Afdekfolie platen",
        "Cryo Tubes": "Cryobuizen",
        "Bottles": "Flessen",
        "Trash Bags": "Afvalzakken",
        "Caps": "Doppen",
        "Reagent Reservoirs": "Reagent reservoirs",
        "Cell Scrapers": "Cel schrapers",
        "Absorbing Paper": "Absorberend papier",
        "Volumetric Labware": "Volumetrisch Glaswerk",
        "Cuvettes": "Cuvetten",
        "Inoculating Loops": "Entogen",
        "Labels and Stickers": "Labels en stickers",
        "Sample Collection Tubes": "Sample buizen",
        "Embedding Cassettes": "Embedding Cassettes",
        "Vials": "Vials",
        "Dispenser Tips": "Dispenser punten",
        "Coverslips": "Dekglaasjes",
        "Blood Collection Needles": "Bloed afnamenaalden",
        "Aluminium Foil Rolls": "Aluminium folie",
        "Syringe Filters": "Spuitfilters",
        "Well Inserts": "Well inserts",
        "Swabs": "Wattenstaafjes",
        "Sleeve Protectors": "Mouwovertrek",
        "Filter Paper": "Filterpapier",
        "Forceps (Reusable)": "Pincet (Herbruikbaar)",
        "Sterilization Bags": "Sterilizatiezakje",
        "Spatulas (Reusable)": "Spatula (Herbruikbaar)",
        "Bottle Top Filters": "Bottle top filters",
        "Spreaders": "Cel spreiders",
        "Microplate Lids": "Multiwell plaatdeksels",
        "Weighing Boats": "Weegschuitjes",
        "Centrifuge Filters": "Centrifugefilters",
        "Cell Counting Slides": "Telkamers",
        "Blades": "Messen",
        "Parafilm": "Parafilm",
        "Chambered Slides": "Objectglazen met kamers",
        "Microtome Blades": "Microtoom messen",
        "Masks": "Mondneus maskers",
        "Cell Strainers": "Celzeven",
        "Fingerprick Lancet": "Vingerprik lancetten",
        "Plate Sealing Mats": "Plaat afdekmatten",
        "Needles": "Naalden",
        "Strawpipettes": "Stropipetten",
        "Glass Inserts": "Glazen inserts",
        "Forceps (Disposable)": "Pincetten (Wegwerp)",
        "Capillaries": "Cappilairen",
        "Labcoats": "Labjassen (Wegwerp)",
        "Printer Paper": "Print papier",
        "Spatulas (Disposable)": "Spatulas (Wegwerp)",
        "Shoe Covers": "Overschoenen",
        "Teststrips": "Teststrips",
        "Tape": "Tape",
        "TORK Paper Roll": "TORK papier",
        "Sealing Film": "Vershoudfolie",
        "Cryo Molds": "Cryo molds",
        "Weighing Paper": "Weegpapier",
        "Lens Cleaning Tissues": "Lens schoonmaaktissue",
        "Safe-Cone Filters": "Safe-Cone filters",
        "Cleaning Tissues": "Schoonmaak tissues",
        "Grinding Chambers": "Maalkamers",
        "Vitrification Devices": "Vitrificatie hulpmiddelen",
    }

    df["categorie_NL"] = df["categorie"].map(label_mapping)

    #group products by category and calculate total item quantities
    df_grouped_aantallen = (
        df.groupby("categorie_NL", as_index=False)["stuks_totaal"]
        .sum()
        .sort_values(by="stuks_totaal", ascending=False)
    )

    #select the 12 categories with the highest item quantities
    top12_aantallen = df_grouped_aantallen.head(12).copy()

    #wrap long category labels for the quantity plot
    top12_aantallen["categorie_NL_split"] = [
        fill(label, width=18)
        for label in top12_aantallen["categorie_NL"]
    ]

    #create the top-12 item quantity plot
    plt.figure(figsize=(8, 8))
    plt.barh(
        top12_aantallen["categorie_NL_split"],
        top12_aantallen["stuks_totaal"],
        color="#5C8D6A",
    )
    plt.yticks(fontsize=12)
    plt.xlabel("Aantal stuks", fontsize=15)
    plt.xticks(fontsize=12)
    plt.title("Top-12 laboratorium disposables - Aantallen", fontsize=20)

    ax = plt.gca()
    plt.gca().invert_yaxis()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    plt.tight_layout()

    #save the item quantity plot
    plt.savefig(
        output_dir / "top12_aantallen.png",
        dpi=300,
        bbox_inches="tight",
    )

    #group products by category and calculate total environmental impact
    df_grouped = (
        df.groupby("categorie_NL", as_index=False)[
            ["milieu_impact_totaal"]
        ]
        .sum()
        .sort_values(by="milieu_impact_totaal", ascending=False)
    )

    #check whether sterilization impact is available
    if "milieu_impact_steriel_totaal" in df.columns:

        #add sterilization impact to the grouped dataframe
        df_grouped_steriel = (
            df.groupby("categorie_NL", as_index=False)[
                ["milieu_impact_steriel_totaal"]
            ]
            .sum()
        )

        #merge sterilization impact with the total environmental impact
        df_grouped = df_grouped.merge(
            df_grouped_steriel,
            on="categorie_NL",
            how="left",
        )

        #calculate the additional impact caused by sterilization
        df_grouped["impact_steriel"] = (
            df_grouped["milieu_impact_steriel_totaal"]
            - df_grouped["milieu_impact_totaal"]
        )

        #sort by total environmental impact including sterilization
        df_grouped = df_grouped.sort_values(
            by="milieu_impact_steriel_totaal",
            ascending=False,
        )

    #select the 12 categories with the highest environmental impact
    top12_milieu = df_grouped.head(12).copy()

    #wrap long category labels for the environmental impact plot
    top12_milieu["categorie_NL_split"] = [
        fill(label, width=18)
        for label in top12_milieu["categorie_NL"]
    ]

    #create the environmental impact plot
    plt.figure(figsize=(8, 8))

    if "milieu_impact_steriel_totaal" in df_grouped.columns:

        #create a stacked environmental impact plot
        plt.barh(
            top12_milieu["categorie_NL_split"],
            top12_milieu["milieu_impact_totaal"],
            color="#386641",
            label="Productie impact",
        )

        plt.barh(
            top12_milieu["categorie_NL_split"],
            top12_milieu["impact_steriel"],
            left=top12_milieu["milieu_impact_totaal"],
            color="#C99700",
            label="Sterilisatie impact",
        )

    else:

        #create a single-bar plot when sterilization impact is unavailable
        plt.barh(
            top12_milieu["categorie_NL_split"],
            top12_milieu["milieu_impact_totaal"],
            color="#386641",
            label="Productie impact",
        )

    plt.yticks(fontsize=12)
    plt.xlabel(r"Milieu-impact ($\text{Kg CO}^2$-eq)", fontsize=15)
    plt.xticks(fontsize=12)
    plt.title("Top-12 laboratorium disposables - Milieu-impact", fontsize=20)

    ax = plt.gca()
    plt.gca().invert_yaxis()

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.xaxis.set_major_formatter(
        FuncFormatter(lambda x, p: f"{int(x):,}".replace(",", "."))
    )

    plt.tight_layout()
    plt.legend(loc="lower right")

    #save the environmental impact plot
    plt.savefig(
        output_dir / "top12_milieu_impact.png",
        dpi=300,
        bbox_inches="tight",
    )


    if "milieu_impact_steriel_totaal" in df.columns:
        #keep categories with a non-zero environmental impact
        df_grouped_cumm = df_grouped[
            df_grouped["milieu_impact_steriel_totaal"] != 0
        ].copy()

        #calculate the total environmental impact
        total = df_grouped_cumm["milieu_impact_steriel_totaal"].sum()

        #calculate the cumulative environmental impact
        df_grouped_cumm["cumulative_sum"] = (
            df_grouped_cumm["milieu_impact_steriel_totaal"].cumsum()
        )

        #calculate the cumulative percentage of total environmental impact
        df_grouped_cumm["cumulative_pct"] = (
            df_grouped_cumm["cumulative_sum"] / total * 100
        )

        #remove categories above 99% cumulative impact
        df_grouped_cumm = df_grouped_cumm[
            df_grouped_cumm["cumulative_pct"] < 99.1
        ]

        #identify categories contributing to approximately the first 80% of impact
        mask_80 = df_grouped_cumm["cumulative_pct"] <= 81

        #create the cumulative environmental impact plot
        plt.figure(figsize=(15, 6))

        #highlight categories within the 80% cumulative impact range
        plt.plot(
            df_grouped_cumm.loc[mask_80, "categorie_NL"],
            df_grouped_cumm.loc[mask_80, "cumulative_pct"],
            marker="o",
            color="#66BB33",
            label="Binnen 80%",
        )

        #plot categories above the 80% cumulative impact range
        plt.plot(
            df_grouped_cumm.loc[~mask_80, "categorie_NL"],
            df_grouped_cumm.loc[~mask_80, "cumulative_pct"],
            marker="o",
            color="lightgray",
            label="Boven 80%",
        )

        #add the 80% reference line
        plt.axhline(80, color="black", linestyle="--", linewidth=1)

        plt.xticks(rotation=45, ha="right")
        plt.ylabel("Cumulatief percentage (%)", fontsize=15)
        plt.yticks(fontsize=13)
        plt.title("Cumulatief Percentage van de milieu-impact", fontsize=20)
        plt.legend()

        #color category labels based on their cumulative impact percentage
        colors = [
            "#66BB33" if pct <= 83 else "black"
            for pct in df_grouped_cumm["cumulative_pct"]
        ]

        plt.xticks(
            ticks=range(len(df_grouped_cumm)),
            labels=df_grouped_cumm["categorie_NL"],
            rotation=45,
            ha="right",
            color="black",
        )

        for tick, c in zip(plt.gca().get_xticklabels(), colors):
            tick.set_color(c)

        plt.tight_layout()

        #save the cumulative environmental impact plot
        plt.savefig(
            output_dir / "cumulative_milieu_impact.png",
            dpi=300,
            bbox_inches="tight",
        )

    else:
        #keep categories with a non-zero environmental impact
        df_grouped_cumm = df_grouped[
            df_grouped["milieu_impact_totaal"] != 0
        ].copy()

        #calculate the total environmental impact
        total = df_grouped_cumm["milieu_impact_totaal"].sum()

        #calculate the cumulative environmental impact
        df_grouped_cumm["cumulative_sum"] = (
            df_grouped_cumm["milieu_impact_totaal"].cumsum()
        )

        #calculate the cumulative percentage of total environmental impact
        df_grouped_cumm["cumulative_pct"] = (
            df_grouped_cumm["cumulative_sum"] / total * 100
        )

        #remove categories above 99% cumulative impact
        df_grouped_cumm = df_grouped_cumm[
            df_grouped_cumm["cumulative_pct"] < 99.1
        ]

        #identify categories contributing to approximately the first 80% of impact
        mask_80 = df_grouped_cumm["cumulative_pct"] <= 81

        #create the cumulative environmental impact plot
        plt.figure(figsize=(15, 6))

        #highlight categories within the 80% cumulative impact range
        plt.plot(
            df_grouped_cumm.loc[mask_80, "categorie_NL"],
            df_grouped_cumm.loc[mask_80, "cumulative_pct"],
            marker="o",
            color="#66BB33",
            label="Binnen 80%",
        )

        #plot categories above the 80% cumulative impact range
        plt.plot(
            df_grouped_cumm.loc[~mask_80, "categorie_NL"],
            df_grouped_cumm.loc[~mask_80, "cumulative_pct"],
            marker="o",
            color="lightgray",
            label="Boven 80%",
        )

        #add the 80% reference line
        plt.axhline(80, color="black", linestyle="--", linewidth=1)

        plt.xticks(rotation=45, ha="right")
        plt.ylabel("Cumulatief percentage (%)", fontsize=15)
        plt.yticks(fontsize=13)
        plt.title("Cumulatief Percentage van de milieu-impact", fontsize=20)
        plt.legend()

        #color category labels based on their cumulative impact percentage
        colors = [
            "#66BB33" if pct <= 83 else "black"
            for pct in df_grouped_cumm["cumulative_pct"]
        ]

        plt.xticks(
            ticks=range(len(df_grouped_cumm)),
            labels=df_grouped_cumm["categorie_NL"],
            rotation=45,
            ha="right",
            color="black",
        )

        for tick, c in zip(plt.gca().get_xticklabels(), colors):
            tick.set_color(c)

        plt.tight_layout()

        #save the cumulative environmental impact plot
        plt.savefig(
            output_dir / "cumulative_milieu_impact.png",
            dpi=300,
            bbox_inches="tight",
        )

    if "milieu_impact_steriel_totaal" in df.columns:
        # Group environmental impact and item quantities by category
        df_full = (
            df.groupby("categorie_NL", as_index=False)[
                ["milieu_impact_steriel_totaal", "stuks_totaal", "gewicht_totaal_kg"]
            ]
            .sum()
        )

        # Rank categories based on total environmental impact
        df_full["rank"] = (
            df_full["milieu_impact_steriel_totaal"]
            .rank(method="dense", ascending=False)
        )

        # Sort categories by total environmental impact
        df_full.sort_values(
            "milieu_impact_steriel_totaal",
            ascending=False,
            inplace=True,
        )

        # Calculate cumulative percentage of total environmental impact
        df_full["cumulative_pct"] = (
            df_full["milieu_impact_steriel_totaal"].cumsum()
            / total
            * 100
        )

        df_full.to_excel(
            output_dir / "lab_disposables_summary.xlsx",
            index=False,
        )

    else:
        # Group environmental impact and item quantities by category
        df_full = (
            df.groupby("categorie_NL", as_index=False)[
                ["milieu_impact_totaal", "stuks_totaal", "gewicht_totaal_kg"]
            ]
            .sum()
        )

        # Rank categories based on total environmental impact
        df_full["rank"] = (
            df_full["milieu_impact_totaal"]
            .rank(method="dense", ascending=False)
        )

        # Sort categories by total environmental impact
        df_full.sort_values(
            "milieu_impact_totaal",
            ascending=False,
            inplace=True,
        )

        # Calculate cumulative percentage of total environmental impact
        df_full["cumulative_pct"] = (
        df_full["milieu_impact_totaal"].cumsum()
            / total
            * 100
        )

        df_full.to_excel(
            output_dir / "lab_disposables_summary.xlsx",
            index=False,
        )

    return None


if __name__ == "__main__":
    df_unclean = pd.read_excel('./results/lab_disposables_full_output.xlsx')
    analyze_lab_disposables(df_unclean)