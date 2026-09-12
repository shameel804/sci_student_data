// python3 generate_pipeline.py prompts "Science Olympiads" --topic basic
// python3 generate_pipeline.py process "Advanced Immunology (MSc)"
// Read the file staging/INSTRUCTIONS.md and follow all instructions. For each task, read the prompt file, generate the quiz JSON following ALL rules, and write the output to the specified output file path.

class Constants {
  static const Map<String, List<Map<String, dynamic>>> allTypes = {
    "Bioprocess Engineering (MSc)": [
      {
        'id': 'scaleup',
        'title': "Process Scale-up",
        'tier': 'free',
        'topics': [
          'Scale-up criteria',
          'Process economics',
          'Regulatory compliance',
          'Technology transfer',
        ],
      },
      {
        'id': 'optimization',
        'title': "Process Optimization",
        'tier': 'free',
        'topics': [
          'Process modeling',
          'Parameter optimization',
          'Quality by design',
          'Process analytical technology',
        ],
      },
      {
        'id': 'purification',
        'title': "Protein Purification",
        'tier': 'vip',
        'topics': [
          'Chromatography methods',
          'Filtration techniques',
          'Crystallization processes',
          'Formulation development',
        ],
      },
    ],

    
  };

}
