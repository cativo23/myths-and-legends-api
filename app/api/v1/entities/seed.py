from sqlalchemy.orm import Session

from app.api.v1.entities.models.category import Category, CategoryName
from app.api.v1.entities.models.entity_type import EntityType, EntityTypeName
from app.api.v1.entities.models.entity import Entity
from app.api.v1.entities.models.characteristic import Characteristic, CharacteristicType
from app.api.v1.entities.models.location import Location
from app.api.v1.entities.models.source import Source, SourceType
from app.api.v1.entities.models.entity_relation import EntityRelation, RelationType


def init_seed_data(db: Session):
    """Seed database with Salvadoran myths and legends entities"""

    # 1. Create categories
    myth = Category(
        name=CategoryName.MYTH,
        description="Traditional stories explaining natural phenomena or cultural beliefs",
    )
    legend = Category(
        name=CategoryName.LEGEND,
        description="Stories passed down through generations, often based on historical events",
    )
    tradition = Category(
        name=CategoryName.TRADITION,
        description="Cultural practices and customs",
    )

    # 2. Create entity types
    character = EntityType(
        name=EntityTypeName.CHARACTER,
        description="Mythological or legendary figures",
    )
    place = EntityType(
        name=EntityTypeName.PLACE,
        description="Locations with mythological or cultural significance",
    )
    object_type = EntityType(
        name=EntityTypeName.OBJECT,
        description="Objects with special significance",
    )
    group = EntityType(
        name=EntityTypeName.GROUP,
        description="Groups or families in legends",
    )
    event = EntityType(
        name=EntityTypeName.EVENT,
        description="Significant mythological events",
    )

    # Add lookup tables first
    db.add_all([myth, legend, tradition, character, place, object_type, group, event])
    db.commit()

    # 3. Create the 8 seed entities with nested relations

    # === La Ciguanaba ===
    ciguanaba = Entity(
        name="La Ciguanaba",
        alternative_names=["La Siguanaba", "La Sihuanaba"],
        category=legend,
        entity_type=character,
        description="A female specter that wanders near rivers and streams at night, luring men to their doom",
        origin="Central figure of Salvadoran mythology, with variations throughout Central America",
        behavior="Appears as a beautiful woman combing her hair by the river, but reveals a horrific face when approached",
        image_url=None,
        is_active=True,
        characteristics=[
            Characteristic(
                type=CharacteristicType.APPEARANCE,
                description="Long black hair covering her face",
            ),
            Characteristic(
                type=CharacteristicType.APPEARANCE,
                description="Beautiful female figure from behind",
            ),
            Characteristic(
                type=CharacteristicType.APPEARANCE,
                description="Horse-like face when seen from front",
            ),
            Characteristic(
                type=CharacteristicType.ABILITY,
                description="Can shapeshift and appear beautiful",
            ),
            Characteristic(
                type=CharacteristicType.WEAKNESS,
                description="Cannot cross running water",
            ),
        ],
        locations=[
            Location(
                department="La Libertad",
                municipality="Talnique",
                place_description="Rivers and streams",
            ),
            Location(
                department="San Salvador", place_description="Lake Ilopango shores"
            ),
        ],
        sources=[
            Source(
                source_type=SourceType.ORAL_TRADITION, title="Salvadoran Folk Tales"
            ),
            Source(
                source_type=SourceType.BOOK,
                title="Leyendas Salvadoreñas",
                author="Various authors",
            ),
        ],
    )

    # === El Cipitillo ===
    cipitillo = Entity(
        name="El Cipitillo",
        alternative_names=["El Cipitío", "El Cipote"],
        category=legend,
        entity_type=character,
        description="A mischievous boy with a large head who is the son of La Ciguanaba",
        origin="Son of La Ciguanaba, cursed to wander eternally as a child",
        behavior="Plays tricks on travelers, helps children in need, known for his distinctive laugh",
        image_url=None,
        is_active=True,
        characteristics=[
            Characteristic(
                type=CharacteristicType.APPEARANCE,
                description="Disproportionately large head",
            ),
            Characteristic(
                type=CharacteristicType.APPEARANCE,
                description="Small body with child-like appearance",
            ),
            Characteristic(
                type=CharacteristicType.ABILITY,
                description="Can disappear and reappear at will",
            ),
            Characteristic(
                type=CharacteristicType.ABILITY,
                description="Superhuman strength despite small size",
            ),
        ],
        locations=[
            Location(
                department="San Miguel", place_description="Mountains and rural areas"
            ),
            Location(department="Usulután", place_description="Coffee plantations"),
        ],
        sources=[
            Source(
                source_type=SourceType.ORAL_TRADITION, title="Tales of El Cipitillo"
            ),
        ],
    )

    # === El Cadejo Blanco ===
    cadejo_blanco = Entity(
        name="El Cadejo Blanco",
        alternative_names=["The White Dog"],
        category=legend,
        entity_type=character,
        description="A protective white dog spirit that guards travelers at night",
        origin="Pre-Columbian belief in guardian spirits, syncretized with Catholic elements",
        behavior="Appears to travelers walking alone at night, protects them from harm and evil spirits",
        image_url=None,
        is_active=True,
        characteristics=[
            Characteristic(
                type=CharacteristicType.APPEARANCE,
                description="Large white dog with glowing eyes",
            ),
            Characteristic(
                type=CharacteristicType.APPEARANCE,
                description="Chains that rattle when he moves",
            ),
            Characteristic(
                type=CharacteristicType.ABILITY, description="Can sense evil and danger"
            ),
            Characteristic(
                type=CharacteristicType.ABILITY, description="Immune to physical harm"
            ),
        ],
        sources=[
            Source(
                source_type=SourceType.ORAL_TRADITION, title="The Legend of the Cadejos"
            ),
        ],
    )

    # === El Cadejo Negro ===
    cadejo_negro = Entity(
        name="El Cadejo Negro",
        alternative_names=["The Black Dog"],
        category=legend,
        entity_type=character,
        description="An evil black dog spirit that attacks and harms travelers",
        origin="Counterpart to El Cadejo Blanco, representing the duality of good and evil",
        behavior="Attacks drunkards and those who walk alone at night, brings bad luck and misfortune",
        image_url=None,
        is_active=True,
        characteristics=[
            Characteristic(
                type=CharacteristicType.APPEARANCE,
                description="Large black dog with red eyes",
            ),
            Characteristic(
                type=CharacteristicType.APPEARANCE, description="Hooves instead of paws"
            ),
            Characteristic(
                type=CharacteristicType.ABILITY, description="Can breathe fire"
            ),
            Characteristic(
                type=CharacteristicType.WEAKNESS,
                description="Repelled by blessed objects",
            ),
        ],
        sources=[
            Source(
                source_type=SourceType.ORAL_TRADITION, title="The Legend of the Cadejos"
            ),
        ],
    )

    # === Volcán Izalco ===
    volcan_izalco = Entity(
        name="Volcán Izalco",
        alternative_names=["Lighthouse of the Pacific"],
        category=myth,
        entity_type=place,
        description="An active volcano known for its continuous eruptions that guided ships at sea",
        origin="Formed in 1770, became one of the most active volcanoes in the world",
        behavior="Erupted continuously from 1770 to 1958, its glow was visible for miles",
        image_url=None,
        is_active=True,
        characteristics=[
            Characteristic(
                type=CharacteristicType.PHYSICAL, description="Height of 1,950 meters"
            ),
            Characteristic(
                type=CharacteristicType.PHYSICAL, description="Perfect cone shape"
            ),
            Characteristic(
                type=CharacteristicType.ABILITY,
                description="Continuous volcanic activity",
            ),
        ],
        locations=[
            Location(
                department="Sonsonate",
                municipality="Sonsonate",
                place_description="Cordillera de Apaneca",
            ),
        ],
        sources=[
            Source(
                source_type=SourceType.DOCUMENT,
                title="Geological Survey of El Salvador",
            ),
            Source(
                source_type=SourceType.WEB,
                title="Smithsonian Global Volcanism Program",
                url="https://volcano.si.edu",
            ),
        ],
    )

    # === La Llorona ===
    la_llorona = Entity(
        name="La Llorona",
        alternative_names=["The Weeping Woman"],
        category=legend,
        entity_type=character,
        description="The ghost of a woman who drowned her children and now wanders crying for them",
        origin="Colonial-era legend with variations throughout Latin America",
        behavior="Wanders near bodies of water at night, crying for her lost children, sometimes abducts children",
        image_url=None,
        is_active=True,
        characteristics=[
            Characteristic(
                type=CharacteristicType.APPEARANCE, description="Woman in white dress"
            ),
            Characteristic(
                type=CharacteristicType.APPEARANCE, description="Long flowing hair"
            ),
            Characteristic(
                type=CharacteristicType.ABILITY,
                description="Heart-wrenching cry heard from far away",
            ),
            Characteristic(
                type=CharacteristicType.WEAKNESS, description="Bound to bodies of water"
            ),
        ],
        locations=[
            Location(department="Santa Ana", place_description="Rivers and lakes"),
            Location(department="Chalatenango", place_description="Lempa River banks"),
        ],
        sources=[
            Source(
                source_type=SourceType.ORAL_TRADITION, title="The Legend of La Llorona"
            ),
        ],
    )

    # === El Duende ===
    el_duende = Entity(
        name="El Duende",
        alternative_names=["The Gnome", "El Enano"],
        category=legend,
        entity_type=character,
        description="A small, mischievous creature that lives in forests and plays tricks on people",
        origin="European folklore adapted to Salvadoran rural culture",
        behavior="Hides objects, makes noises in the forest, sometimes helps, sometimes harms",
        image_url=None,
        is_active=True,
        characteristics=[
            Characteristic(
                type=CharacteristicType.APPEARANCE,
                description="Small humanoid, about 3 feet tall",
            ),
            Characteristic(
                type=CharacteristicType.APPEARANCE, description="Large sombrero hat"
            ),
            Characteristic(
                type=CharacteristicType.APPEARANCE, description="Backwards feet"
            ),
            Characteristic(
                type=CharacteristicType.ABILITY, description="Can become invisible"
            ),
            Characteristic(
                type=CharacteristicType.ABILITY,
                description="Whistles to attract attention",
            ),
        ],
        locations=[
            Location(department="Morazán", place_description="Forests and mountains"),
            Location(department="Cabañas", place_description="Rural areas"),
        ],
        sources=[
            Source(source_type=SourceType.ORAL_TRADITION, title="Tales of El Duende"),
        ],
    )

    # === La Familia Girola ===
    familia_girola = Entity(
        name="La Familia Girola",
        alternative_names=["The Girola Family"],
        category=legend,
        entity_type=group,
        description="A wealthy family cursed to wander as ghosts in their former mansion",
        origin="Based on a real family from the colonial era in Sonsonate",
        behavior="Appear in their mansion at night, reliving their last moments",
        image_url=None,
        is_active=True,
        characteristics=[
            Characteristic(
                type=CharacteristicType.APPEARANCE,
                description="Dressed in colonial-era clothing",
            ),
            Characteristic(
                type=CharacteristicType.APPEARANCE,
                description="Transparent, ghostly figures",
            ),
            Characteristic(
                type=CharacteristicType.WEAKNESS, description="Bound to their mansion"
            ),
        ],
        locations=[
            Location(
                department="Sonsonate",
                municipality="Sonsonate",
                place_description="Historic center mansion",
            ),
        ],
        sources=[
            Source(
                source_type=SourceType.BOOK,
                title="Legends of Sonsonate",
                author="Local historians",
            ),
            Source(
                source_type=SourceType.ORAL_TRADITION,
                title="The Curse of the Girola Family",
            ),
        ],
    )

    # Add all entities with their nested relations
    db.add_all(
        [
            ciguanaba,
            cipitillo,
            cadejo_blanco,
            cadejo_negro,
            volcan_izalco,
            la_llorona,
            el_duende,
            familia_girola,
        ]
    )
    db.flush()  # Get IDs for all entities

    # === Create Relations ===
    # La Ciguanaba -> El Cipitillo (Mother-Child)
    relation_ciguanaba_cipitillo = EntityRelation(
        entity_origin_id=ciguanaba.id,
        entity_destination_id=cipitillo.id,
        relation_type=RelationType.MOTHER_CHILD,
        description="El Cipitillo is the cursed son of La Ciguanaba",
    )

    # El Cipitillo -> La Ciguanaba (Mother-Child reverse)
    relation_cipitillo_ciguanaba = EntityRelation(
        entity_origin_id=cipitillo.id,
        entity_destination_id=ciguanaba.id,
        relation_type=RelationType.MOTHER_CHILD,
        description="La Ciguanaba is the mother of El Cipitillo",
    )

    # El Cadejo Blanco <-> El Cadejo Negro (Enemies - bidirectional)
    relation_cadejos_enemies = EntityRelation(
        entity_origin_id=cadejo_blanco.id,
        entity_destination_id=cadejo_negro.id,
        relation_type=RelationType.ENEMIES,
        description="The Cadejos represent the eternal struggle between good and evil",
    )
    relation_cadejos_enemies_reverse = EntityRelation(
        entity_origin_id=cadejo_negro.id,
        entity_destination_id=cadejo_blanco.id,
        relation_type=RelationType.ENEMIES,
        description="The Cadejos represent the eternal struggle between good and evil",
    )

    # Add relations
    db.add_all(
        [
            relation_ciguanaba_cipitillo,
            relation_cipitillo_ciguanaba,
            relation_cadejos_enemies,
            relation_cadejos_enemies_reverse,
        ]
    )

    db.commit()
