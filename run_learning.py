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

# first_draft = valueiteration2.Draft(14, roster, 16, "HALF", 14 * 16 * 100)
# print("Running drafts...")
# first_draft.run_draft()
# print("Getting results...")
# first_draft.get_results()

# first_draft = valueiteration2.Draft(14, roster, 16, "HALF", 14 * 16 * 10000)
# print("Running drafts...")
# first_draft.run_draft_together()
# print("Getting results...")
# first_draft.get_results_together()

first_draft = valueiteration2.Draft(
    12, roster, 16, "HALF", 12 * 16 * 100, "data/iterated_rosters_pickled.pkl")
# print("Getting qbs...")
# first_draft.test_rosters_position("qb")
# print("Getting rbs...")
# first_draft.test_rosters_position("rb")
# print("Getting wrs...")
# first_draft.test_rosters_position("wr")
# print("Getting tes...")
# first_draft.test_rosters_position("te")
first_draft.test_rosters_rbwr()
