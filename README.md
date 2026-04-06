# Track Anything (TA) Clone API

This is a sample Python FastApi backend built to demonstrate the core domain concepts of a flexible **"Track Anything"** work management system.

## Core Capabilities

The objective of this project is to build a system capable of:
> "...creating powerful, flexible, and smart attributes (i.e. Custom Fields, Custom Task Types) that reflect the real-world properties involved in work, and by mapping these attributes globally to enrich and unlock the unique power of the Work Graph."

This API exactly implements that capability:
1. **Custom Fields (`/custom-fields`)**: Build custom properties on the fly. You can define fields of various types: String, Enum (dropdowns), Boolean, Numbers, Dates.
2. **Custom Task Types (`/task-types`)**: You can define entirely new kinds of items to track (e.g. "Software Bug", "Interview Candidate", "Marketing Campaign") and map specific Custom Fields that are *only* applicable to that type.
3. **Tasks (`/tasks`)**: The actual objects in the graph that ingest these properties. It includes runtime validation ensuring that assigned Custom Fields follow the constraints (e.g. correct type and within enum options) and belong to the correct Custom Task Type.

## Setup and Running

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the development server:
   ```bash
   uvicorn main:app --reload
   ```

3. Open your browser to `http://127.0.0.1:8000/docs` to test it using the interactive Swagger UI.

## API Flow Example

Using the Swagger UI (or curl), you can mock out a real-world scenario:

1. **Create an ENUM field** called "T-Shirt Size" with options ["Small", "Medium", "Large"].
2. **Create a NUMBER field** called "Story Points".
3. **Create a Task Type** called "Sprint Feature" and map the UUIDs of the two Custom Fields you just created.
4. **Create a Task** with `task_type_id` set to the "Sprint Feature" UUID, and feed it a `.custom_fields` dictionary of your custom IDs and their respective values (e.g. {"field_uuid_here": "Medium"}). The API will validate it against the dynamic schemas!
