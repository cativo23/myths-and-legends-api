from sqlalchemy.orm import Session

from app.api.v1.domains.entities.models.category import Category, CategoryName
from app.api.v1.domains.entities.models.entity_type import EntityType, EntityTypeName
from app.api.v1.domains.entities.models.entity import Entity
from app.api.v1.domains.entities.models.characteristic import (
    Characteristic,
    CharacteristicType,
)
from app.api.v1.domains.entities.models.location import Location
from app.api.v1.domains.entities.models.source import Source, SourceType
from app.api.v1.domains.entities.models.entity_relation import (
    EntityRelation,
    RelationType,
)


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

    # === La Carreta Chillona ===
    carreta_chillona = Entity(
        name="La Carreta Chillona",
        alternative_names=["La Carreta Bruja"],
        category=legend,
        entity_type=object_type,
        description="A phantom ox-cart with wooden wheels that rolls down rural roads at night, announced by a horrific screeching sound",
        origin="Salvadoran rural oral tradition; thematically similar phantom-cart legends exist in Nicaragua (La Carretanagua) but the Salvadoran version is independently documented as its own tradition",
        behavior="Heard before it is seen — the screeching of its wooden wheels announces its approach; believed to collect the souls of those who wander lonely roads at night",
        image_url=None,
        is_active=True,
        characteristics=[
            Characteristic(
                type=CharacteristicType.APPEARANCE,
                description="Wooden-wheeled ox-cart, heard as a screeching/creaking sound before it appears",
            ),
            Characteristic(
                type=CharacteristicType.ABILITY,
                description="Said to collect the souls of late-night travelers who encounter it",
            ),
        ],
        sources=[
            Source(
                source_type=SourceType.BOOK,
                title="Mitos y leyendas de El Salvador",
                author="Omar Nipolan",
            ),
            Source(
                source_type=SourceType.WEB,
                title="Las 30 Mejores Leyendas de El Salvador",
                url="https://elsalvadorviajar.com/en/traditions/legends/",
            ),
        ],
    )

    # === El Justo Juez de la Noche ===
    justo_juez = Entity(
        name="El Justo Juez de la Noche",
        alternative_names=["El Justo Juez"],
        category=legend,
        entity_type=character,
        description="A headless specter who rides a black horse (or walks with giant strides) along rural roads at night, questioning travelers and punishing wrongdoers",
        origin="Salvadoran rural oral tradition, colonial-era folk figure",
        behavior="Patrols rural roads at night, stops travelers to question them, and whips bandits, drunkards, and curfew-breakers",
        image_url=None,
        is_active=True,
        characteristics=[
            Characteristic(
                type=CharacteristicType.APPEARANCE,
                description="Headless figure dressed in black, with smoke rising where the head should be",
            ),
            Characteristic(
                type=CharacteristicType.APPEARANCE,
                description="Rides a black horse, or is described taking giant strides",
            ),
            Characteristic(
                type=CharacteristicType.ABILITY,
                description="Enforces order at night, whipping wrongdoers encountered on the road",
            ),
        ],
        sources=[
            Source(
                source_type=SourceType.WEB,
                title="Justo Juez de la noche",
                url="https://es.wikipedia.org/wiki/Justo_Juez_de_la_noche",
            ),
            Source(
                source_type=SourceType.BOOK,
                title="Mitos y leyendas de El Salvador",
                author="Omar Nipolan",
            ),
        ],
    )

    # === Laguna de Olomega ===
    laguna_olomega = Entity(
        name="Laguna de Olomega",
        alternative_names=[],
        category=legend,
        entity_type=place,
        description="A lake in eastern El Salvador associated with a siren/mermaid at Isla Olomegón whose songs lure and madden nighttime fishermen, and with 'Piedras del Diablo' petroglyphs linked to a historical site where supernatural sounds are reported",
        origin="San Miguel / La Unión border region",
        behavior="The siren's singing is said to lure and disorient fishermen who are out on the lake at night; unexplained sounds are reported near the Piedras del Diablo petroglyphs",
        image_url=None,
        is_active=True,
        characteristics=[
            Characteristic(
                type=CharacteristicType.PHYSICAL,
                description="Freshwater lake spanning San Miguel and La Unión departments",
            ),
            Characteristic(
                type=CharacteristicType.ABILITY,
                description="Siren's song lures and disorients nighttime fishermen",
            ),
        ],
        locations=[
            Location(
                department="San Miguel",
                municipality="Chirilagua",
                place_description="Isla Olomegón, where the siren legend is set",
            ),
            Location(
                department="La Unión",
                municipality="El Carmen",
                place_description="Shore of the lake",
            ),
        ],
        sources=[
            Source(
                source_type=SourceType.WEB,
                title="Laguna de Olomega",
                url="https://es.wikipedia.org/wiki/Laguna_de_Olomega",
            ),
            Source(
                source_type=SourceType.WEB,
                title="Las 5 lagunas más misteriosas de El Salvador",
                url="https://www.elsalvador.com/turismo/rutas-y-aventuras/leyendas-lagunas-el-salvador/1249040/2025/",
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
            carreta_chillona,
            justo_juez,
            laguna_olomega,
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
