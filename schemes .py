from fastapi import (
    APIRouter,
    Form,
    HTTPException,
    Request
)

from fastapi.responses import (
    JSONResponse
)

from app.schemas import PromptRequest

from app.gemini_flash import (
    generate_outline
)

from app.gemini_pro import (
    generate_story
)

from app.image_generator import (
    generate_image
)

from app.layout_builder import (
    build_comic_layout
)

from app.exporters import (
    save_pdf
)


router = APIRouter()


def create_title(
    character_name,
    story_prompt
):

    short_prompt = (
        " ".join(
            story_prompt.split()
        )
    )[:55]

    return (
        f"{character_name}'s Adventure "
        f"— {short_prompt}"
    )


def generate_complete_comic(
    data
):

    # STEP 1
    outline = generate_outline(

        data.story_prompt,

        data.character_name,

        data.setting,

        data.tone,

        data.art_style
    )


    # STEP 2
    story = generate_story(

        outline,

        data.story_prompt,

        data.character_name,

        data.setting,

        data.tone,

        data.art_style
    )


    # STEP 3
    image_paths = []

    for panel in story:

        image = generate_image(

            panel["image_prompt"],

            panel["panel_number"]
        )

        image_paths.append(
            image
        )


    # STEP 4
    layout = build_comic_layout(

        story,

        image_paths
    )


    # STEP 5
    title = create_title(

        data.character_name,

        data.story_prompt
    )


    # STEP 6
    pdf_url = save_pdf(

        layout,

        title
    )


    return (
        title,
        layout,
        pdf_url
    )


@router.get("/")
async def home(
    request: Request
):

    return request.app.state.templates.TemplateResponse(

        "index.html",

        {
            "request": request
        }
    )


@router.post("/generate")
async def generate(

    request: Request,

    story_prompt: str = Form(...),

    character_name: str = Form(...),

    setting: str = Form(...),

    tone: str = Form(...),

    art_style: str = Form(...)
):

    data = PromptRequest(

        story_prompt=story_prompt,

        character_name=character_name,

        setting=setting,

        tone=tone,

        art_style=art_style
    )

    try:

        title, layout, pdf_url = (
            generate_complete_comic(
                data
            )
        )

        return (
            request
            .app
            .state
            .templates
            .TemplateResponse(

                "comic_preview.html",

                {
                    "request": request,

                    "title": title,

                    "layout": layout,

                    "pdf_url": pdf_url
                }
            )
        )

    except Exception as error:

        return (
            request
            .app
            .state
            .templates
            .TemplateResponse(

                "index.html",

                {
                    "request": request,

                    "error": str(error),

                    "form": data.model_dump()
                },

                status_code=500
            )
        )


@router.post(
    "/generate-comic/json"
)
async def generate_json(
    data: PromptRequest
):

    try:

        title, layout, pdf_url = (
            generate_complete_comic(
                data
            )
        )

        return JSONResponse(

            {
                "success": True,

                "title": title,

                "panels": layout,

                "pdf_url": pdf_url
            }
        )

    except Exception as error:

        raise HTTPException(

            status_code=500,

            detail=str(error)
        )


@router.get(
    "/export-success"
)
async def export_success(

    request: Request,

    pdf: str = ""
):

    return (
        request
        .app
        .state
        .templates
        .TemplateResponse(

            "export_success.html",

            {
                "request": request,

                "pdf_url": pdf
            }
        )
    )


@router.get(
    "/test-image"
)
async def test_image(

    prompt: str =
    "A brave fox in an enchanted forest, comic book art"
):

    try:

        image_url = generate_image(

            prompt,

            0
        )

        return {

            "success": True,

            "image_url": image_url
        }

    except Exception as error:

        raise HTTPException(

            status_code=500,

            detail=str(error)
        )


@router.get("/health")
async def health():

    return {
        "status": "ok"
    }