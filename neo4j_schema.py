NEO4J_SCHEMA = {
  "nodes": [
    {
      "label": "Satellite",
      "properties": [
        {
          "name": "id",
          "type": "STRING"
        },
        {
          "name": "created_at",
          "type": "STRING"
        }
      ]
    },
    {
      "label": "Sensor",
      "properties": [
        {
          "name": "id",
          "type": "STRING"
        },
        {
          "name": "created_at",
          "type": "STRING"
        }
      ]
    },
    {
      "label": "Organization",
      "properties": [
        {
          "name": "id",
          "type": "STRING"
        },
        {
          "name": "created_at",
          "type": "STRING"
        }
      ]
    },
    {
      "label": "Page",
      "properties": [
        {
          "name": "filename",
          "type": "STRING"
        },
        {
          "name": "title",
          "type": "STRING"
        }
      ]
    }
  ],
  "relationships": []
}

# Add your CYPHER_EXAMPLES here if needed