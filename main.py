from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from uuid import uuid4, UUID
from enum import Enum

app = FastAPI(
    title="Flexible Work Management API",
    description="Sample backend demonstrating Custom Fields, Custom Task Types and dynamic schema construction.",
    version="1.0.0"
)

# --- ENUMS & SCHEMAS ---

class FieldType(str, Enum):
    TEXT = "text"
    NUMBER = "number"
    ENUM = "enum"
    BOOLEAN = "boolean"
    DATE = "date"

# 1. Custom Fields Definition
class CustomFieldDefBase(BaseModel):
    name: str = Field(..., description="Name of the custom field (e.g., 'Priority', 'Cost')")
    type: FieldType
    options: Optional[List[str]] = Field(default=None, description="Only for ENUM type. Ex: ['High', 'Medium', 'Low']")

class CustomFieldDefCreate(CustomFieldDefBase):
    pass

class CustomFieldDef(CustomFieldDefBase):
    id: UUID = Field(default_factory=uuid4)

# 2. Custom Task Types
class TaskTypeBase(BaseModel):
    name: str = Field(..., description="Name of the task type (e.g., 'Bug', 'Milestone', 'Feature')")
    icon: Optional[str] = None
    allowed_custom_fields: List[UUID] = Field(default=[], description="List of Custom Field IDs that apply to this Task Type.")

class TaskTypeCreate(TaskTypeBase):
    pass

class TaskType(TaskTypeBase):
    id: UUID = Field(default_factory=uuid4)

# 3. Tasks
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = ""
    task_type_id: Optional[UUID] = None
    custom_fields: Dict[str, Any] = Field(
        default={}, 
        description="Key is the Custom Field ID (as string), Value is the actual assigned value. The value must match the field's type/options."
    )

class TaskCreate(TaskBase):
    pass

class Task(TaskBase):
    id: UUID = Field(default_factory=uuid4)


# --- IN-MEMORY DATABASE ---
db_custom_fields: Dict[UUID, CustomFieldDef] = {}
db_task_types: Dict[UUID, TaskType] = {}
db_tasks: Dict[UUID, Task] = {}


# --- APP ROUTES ---

@app.get("/")
def read_root():
    return {"message": "Welcome to the Track Anything API. Check out /docs for interactive Swagger documentation."}

# --- CUSTOM FIELDS ENDPOINTS ---

@app.post("/custom-fields", response_model=CustomFieldDef, status_code=status.HTTP_201_CREATED)
def create_custom_field(field_def_in: CustomFieldDefCreate):
    if field_def_in.type == FieldType.ENUM and not field_def_in.options:
        raise HTTPException(status_code=400, detail="ENUM fields must define a list of options.")
    
    new_field = CustomFieldDef(**field_def_in.model_dump())
    db_custom_fields[new_field.id] = new_field
    return new_field

@app.get("/custom-fields", response_model=List[CustomFieldDef])
def get_custom_fields():
    return list(db_custom_fields.values())

@app.get("/custom-fields/{field_id}", response_model=CustomFieldDef)
def get_custom_field(field_id: UUID):
    if field_id not in db_custom_fields:
        raise HTTPException(status_code=404, detail="Custom Field not found.")
    return db_custom_fields[field_id]

# --- TASK TYPES ENDPOINTS ---

@app.post("/task-types", response_model=TaskType, status_code=status.HTTP_201_CREATED)
def create_task_type(task_type_in: TaskTypeCreate):
    # Validate that all provided custom fields exist
    for cf_id in task_type_in.allowed_custom_fields:
        if cf_id not in db_custom_fields:
            raise HTTPException(status_code=400, detail=f"Custom Field ID {cf_id} does not exist.")
            
    new_task_type = TaskType(**task_type_in.model_dump())
    db_task_types[new_task_type.id] = new_task_type
    return new_task_type

@app.get("/task-types", response_model=List[TaskType])
def get_task_types():
    return list(db_task_types.values())

# --- TASKS ENDPOINTS ---

def validate_task_custom_fields(task: TaskCreate):
    """
    Core engine for 'Track Anything'. Resolves and validates field rules vs data.
    """
    if not task.task_type_id:
        return # If no task type, skip validation for simplicity, or we could strict-enforce. Let's allow basic tasks.
        
    if task.task_type_id not in db_task_types:
        raise HTTPException(status_code=400, detail="Task Type not found.")
        
    task_type = db_task_types[task.task_type_id]
    allowed_fields_str = [str(cf_id) for cf_id in task_type.allowed_custom_fields]
    
    for field_id_str, field_val in task.custom_fields.items():
        if field_id_str not in allowed_fields_str:
            raise HTTPException(status_code=400, detail=f"Field {field_id_str} is not allowed for task type {task_type.name}.")
            
        field_def = db_custom_fields[UUID(field_id_str)]
        
        # Validations based on type enum
        if field_def.type == FieldType.NUMBER and not isinstance(field_val, (int, float)):
            raise HTTPException(status_code=400, detail=f"Field {field_def.name} must be a number.")
        if field_def.type == FieldType.TEXT and not isinstance(field_val, str):
            raise HTTPException(status_code=400, detail=f"Field {field_def.name} must be text.")
        if field_def.type == FieldType.BOOLEAN and not isinstance(field_val, bool):
            raise HTTPException(status_code=400, detail=f"Field {field_def.name} must be a boolean.")
        if field_def.type == FieldType.ENUM and field_val not in field_def.options:
            raise HTTPException(status_code=400, detail=f"Field {field_def.name} value '{field_val}' provides an invalid option. Allowed: {field_def.options}")


@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(task_in: TaskCreate):
    validate_task_custom_fields(task_in)
    new_task = Task(**task_in.model_dump())
    db_tasks[new_task.id] = new_task
    return new_task

@app.get("/tasks", response_model=List[Task])
def get_tasks():
    return list(db_tasks.values())
