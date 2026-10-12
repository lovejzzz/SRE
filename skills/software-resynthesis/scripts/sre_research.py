"""Discovery coverage and discriminating experiments; no network or code execution."""
import json
from pathlib import Path
from sre_common import require, read, write_new, digest, text, object_v1, difference


def artifact(root, relative):
    require(text(relative) and not Path(relative).is_absolute(), "Expected relative artifact path")
    path = (root / relative).resolve()
    require(path.is_relative_to(root) and path.is_file(), f"Missing/escaped artifact: {relative}")
    return path


def records(values, label):
    require(isinstance(values, list), f"Expected {label} list")
    result = {}
    for value in values:
        require(isinstance(value, dict) and text(value.get("id")), f"Invalid {label} record")
        require(value["id"] not in result, f"Duplicate {label}: {value['id']}")
        result[value["id"]] = value
    return result


def inputs(workspace):
    root = Path(workspace).resolve()
    project, research = read(root / "project.json"), read(root / "research.json")
    object_v1(project)
    object_v1(research)
    return root, project, research


def inventory(root, project, research):
    scope = research.get("scope")
    require(isinstance(scope, dict), "Missing research scope")
    for key in ("description", "source_build", "target"):
        require(text(scope.get(key)), f"Missing scope {key}")
    require(scope["source_build"] != "unresolved", "Pin a source build before sealing")
    require(scope.get("claim") in ("milestone", "full"), "Invalid scope claim")
    features = records(project.get("features"), "features")
    require(isinstance(scope.get("features"), list) and scope["features"] and
            all(text(f) and f in features for f in scope["features"]), "Invalid scope feature IDs")
    require(len(set(scope["features"])) == len(scope["features"]), "Duplicate scope feature IDs")
    require(set(scope["features"]) == set(features), "Scope and project feature inventory differ")
    surveys = records(research.get("surveys"), "surveys")
    require(surveys, "No discovery surveys")
    evidence, findings, kinds = [], [], set()
    mapped = set()
    for sid, survey in surveys.items():
        require(survey.get("kind") in ("docs", "ui", "api", "runtime", "source", "files"), "Invalid survey kind")
        require(type(survey.get("required")) is bool, "Survey requires explicit required boolean")
        require(survey.get("status") in ("complete", "pending", "unavailable"), "Invalid survey status")
        if survey["status"] != "complete":
            require(text(survey.get("reason")), "Incomplete survey needs a reason")
            if survey["required"]:
                findings.append(f"Required survey incomplete: {sid}")
            evidence.append({"survey": survey, "sha256": None})
            continue
        path = artifact(root, survey.get("artifact"))
        data = read(path)
        object_v1(data)
        require(data.get("source_build") == scope["source_build"], f"Survey build mismatch: {sid}")
        require(text(data.get("source")) and text(data.get("scope_note")), f"Missing survey provenance: {sid}")
        items = records(data.get("items"), "inventory items")
        require(items, f"Empty completed survey: {sid}")
        kinds.add(survey["kind"])
        for iid, item in items.items():
            require(text(item.get("label")), "Inventory item needs label")
            fid = item.get("feature")
            if text(fid) and fid in features:
                mapped.add(fid)
            elif item.get("disposition") == "excluded" and text(item.get("reason")):
                if scope["claim"] == "full":
                    findings.append(f"Full-scope claim excludes discovered item: {sid}/{iid}")
            else:
                findings.append(f"Unmapped discovered item: {sid}/{iid}")
        evidence.append({"survey": survey, "sha256": digest(path)})
    # Multiple methods improve discovery; they do not prove exhaustive feature discovery.
    if len(kinds) < 2:
        findings.append("Discovery needs at least two completed surface kinds")
    for fid in features:
        if fid not in mapped:
            findings.append(f"Feature has no discovery evidence: {fid}")
    graph = {}
    for fid, feature in features.items():
        deps = feature.get("depends_on", [])
        require(isinstance(deps, list) and all(text(x) and x in features for x in deps), f"Invalid dependencies: {fid}")
        parent = feature.get("parent")
        require(parent is None or (text(parent) and parent in features), f"Invalid parent: {fid}")
        graph[fid] = deps + ([parent] if parent else [])
    active, done = set(), set()
    def visit(fid):
        require(fid not in active, f"Feature dependency/hierarchy cycle: {fid}")
        if fid in done:
            return
        active.add(fid)
        for dep in graph[fid]:
            visit(dep)
        active.remove(fid)
        done.add(fid)
    for fid in features:
        visit(fid)
    policies = []
    for vid, validation in records(project.get("validations"), "validations").items():
        if validation.get("kind") == "domain":
            policy = validation.get("policy")
            policies.append({"id": vid, "policy": policy, "sha256": digest(artifact(root, policy))})
    planned_questions = []
    for q in records(research.get("questions"), "questions").values():
        planned = {k: v for k, v in q.items() if k != "experiments"}
        planned["experiments"] = [{k: v for k, v in e.items() if k != "observation"}
                                  for e in records(q.get("experiments"), "experiments").values()]
        planned_questions.append(planned)
    frozen = {"schema_version": 1, "scope": scope, "surveys": evidence,
              "project_intent": {k: project.get(k) for k in ("request", "source", "target")},
              "domain_policies": policies, "question_contracts": planned_questions,
              "features": [{k: f.get(k) for k in ("id", "description", "mode", "parent", "depends_on", "acceptance")}
                           for f in features.values()]}
    return frozen, findings


def seal(workspace, out):
    root, project, research = inputs(workspace)
    frozen, findings = inventory(root, project, research)
    require(not findings, "Cannot seal incomplete inventory: " + "; ".join(findings))
    destination = (root / out).resolve()
    require(not Path(out).is_absolute() and destination.is_relative_to(root), "Baseline must stay inside workspace")
    write_new(destination, frozen)
    return {"baseline": out, "sha256": digest(destination), "claim": frozen["scope"]["claim"]}


def pointer(value, selector):
    require(isinstance(selector, str) and (selector == "" or selector.startswith("/")), "Invalid JSON pointer")
    for token in selector.split("/")[1:]:
        require(all(part and part[0] in "01" for part in token.split("~")[1:]), "Invalid JSON pointer escape")
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(value, list):
            require(token.isascii() and token.isdigit() and (token == "0" or not token.startswith("0")) and int(token) < len(value), "Invalid array pointer")
            value = value[int(token)]
        else:
            require(isinstance(value, dict) and token in value, "Missing observation pointer")
            value = value[token]
    return value


def experiments(root, project, research):
    features = records(project.get("features"), "features")
    questions = records(research.get("questions"), "questions")
    summaries, queue, problems = [], [], []
    for qid, question in questions.items():
        require(text(question.get("question")) and text(question.get("feature")) and question["feature"] in features, f"Invalid question: {qid}")
        require(type(question.get("blocking")) is bool, "Question needs blocking boolean")
        require(type(question.get("impact")) is int and 1 <= question["impact"] <= 5, "Impact must be 1..5")
        hypotheses = records(question.get("hypotheses"), "hypotheses")
        require(len(hypotheses) >= 2 and all(text(h.get("explanation")) for h in hypotheses.values()),
                "Research question needs competing explanations")
        candidates = set(hypotheses)
        observed_count = 0
        for eid, experiment in records(question.get("experiments"), "experiments").items():
            predictions = experiment.get("predictions")
            require(isinstance(predictions, dict) and set(predictions) == set(hypotheses), "Predictions must cover every hypothesis")
            require(isinstance(experiment.get("input"), dict) and experiment["input"], "Experiment needs input")
            cost = experiment.get("cost")
            require(type(cost) is int and 1 <= cost <= 5, "Experiment cost must be 1..5")
            observation = experiment.get("observation")
            if observation is not None:
                require(isinstance(observation, dict), "Invalid observation")
                captured_path = artifact(root, observation.get("artifact"))
                require(observation.get("sha256") == digest(captured_path), "Missing or stale observation sha256; fingerprint the reviewed capture")
                captured = read(captured_path)
                object_v1(captured)
                provenance = captured.get("provenance")
                require(isinstance(provenance, dict) and provenance.get("kind") == "source-runtime" and
                        provenance.get("build") == research["scope"]["source_build"], "Observation must match source runtime/build")
                value = pointer(captured, observation.get("pointer"))
                candidates &= {hid for hid, prediction in predictions.items() if difference(prediction, value) is None}
                observed_count += 1
        for eid, experiment in records(question["experiments"], "experiments").items():
            if experiment.get("observation") is not None or len(candidates) <= 1:
                continue
            groups = {}
            for hid in candidates:
                prediction = json.dumps(experiment["predictions"][hid], sort_keys=True, allow_nan=False)
                groups[prediction] = groups.get(prediction, 0) + 1
            # Uniform-prior expected elimination; heuristic, not measured certainty.
            gain = 1 - sum(n * n for n in groups.values()) / len(candidates) ** 2
            if gain > 0:
                queue.append({"question": qid, "experiment": eid, "input": experiment["input"],
                              "score": round(question["impact"] * gain / experiment["cost"], 6),
                              "blocking": question["blocking"]})
        status = "contradiction" if not candidates else "resolved" if observed_count and len(candidates) == 1 else "open"
        summaries.append({"id": qid, "status": status, "surviving_hypotheses": sorted(candidates)})
        if status == "contradiction" or (question["blocking"] and status != "resolved"):
            problems.append(f"Research question {status}: {qid}")
    queue.sort(key=lambda x: (-x["blocking"], -x["score"], x["question"], x["experiment"]))
    return {"questions": summaries, "next_experiments": queue, "problems": problems}


def audit(workspace):
    root, project, research = inputs(workspace)
    frozen, problems = inventory(root, project, research)
    baseline = artifact(root, project.get("research_baseline", "research-baseline.json"))
    if difference(read(baseline), frozen) is not None:
        problems.append("Discovery baseline is stale: scope, feature contract, or source inventory changed")
    plan = experiments(root, project, research)
    problems.extend(plan["problems"])
    return {"schema_version": 1, "research_ready": not problems, "claim": frozen["scope"]["claim"],
            "problems": problems, "questions": plan["questions"], "next_experiments": plan["next_experiments"],
            "limitation": "Audits declared discovery surfaces; cannot prove absence of undiscovered features."}
