import qlearning2
import valueiteration2

ESPN_setting = {"num_teams": 10, "num_rounds": 14}

roster = {}
roster["qb"] = set()
roster["rb"] = set()
roster["wr"] = set()
roster["te"] = set()
roster["dst"] = set()
roster["k"] = set()
# roster["qb"] = []
# roster["rb"] = []
# roster["wr"] = []
# roster["te"] = []
# roster["dst"] = []
# roster["k"] = []
# first_draft = qlearning2.Draft(14, roster, 16, "HALF", 14 * 16 * 100)
first_draft = valueiteration2.Draft(14, roster, 16, "HALF", 14 * 16 * 100)
print("Running drafts...")
first_draft.run_draft()
print("Getting results...")
first_draft.get_results()
