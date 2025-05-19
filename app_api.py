from fastapi import FastAPI
from typing import Optional
from utils import get_chain, save_to_mongo, save_to_github
from config import courses_collection

app = FastAPI(title="Moodle Pedagogical Assistant API")
chain = get_chain()

@app.get("/generate")
async def generate_scenario(course_title: str, level: Optional[str] = "intermédiaire"):
    try:
        full_title = f"{course_title} (niveau {level})"
        response = chain.run({"titre_cours": full_title})
        mongo_id = save_to_mongo(course_title, response, level)
        github_file = save_to_github(course_title, response)
        return {
            "scenario": response,
            "mongo_id": str(mongo_id),
            "github_file": github_file
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/scenarios")
async def get_scenarios(limit: int = 10):
    try:
        scenarios = list(courses_collection.find().sort("created_at", -1).limit(limit))
        for s in scenarios:
            s["_id"] = str(s["_id"])
        return {"scenarios": scenarios}
    except Exception as e:
        return {"error": str(e)}
