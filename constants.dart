// python3 generate_pipeline.py prompts "Drug Design (MSc)" --topic basic
// python3 generate_pipeline.py process "Advanced Immunology (MSc)"
// Read the file staging/INSTRUCTIONS.md and follow all instructions. For each task, read the prompt file, generate the quiz JSON following ALL rules, and write the output to the specified output file path.

class Constants {
  static const Map<String, List<Map<String, dynamic>>> allTypes = {
     "Nanochemistry (MSc)": [
      {
        'id': 'nanoparticles',
        'title': "Nanoparticles",
        'tier': 'free',
        'topics': [
          'Nanoparticle synthesis',
          'Core-shell structures',
          'Functionalization methods',
          'Characterization techniques',
        ],
      },
      {
        'id': 'synthesis',
        'title': "Nanomaterial Synthesis",
        'tier': 'free',
        'topics': [
          'Bottom-up approaches',
          'Top-down methods',
          'Self-assembly processes',
          'Template synthesis',
        ],
      },
      {
        'id': 'applications',
        'title': "Nanotechnology Applications",
        'tier': 'vip',
        'topics': [
          'Characterization methods',
          'Size determination',
          'Surface analysis',
          'Structural characterization',
        ],
      },
    ],
    "Advanced Quantum Mechanics (MSc)": [
      {
        'id': 'relativistic',
        'title': "Relativistic Quantum Mechanics",
        'tier': 'free',
        'topics': [
          'Dirac equation',
          'Relativistic effects',
          'Quantum electrodynamics',
          'Field quantization',
        ],
      },
      {
        'id': 'field',
        'title': "Quantum Field Theory",
        'tier': 'free',
        'topics': [
          'Canonical quantization',
          'Path integral formulation',
          'Gauge theories',
          'Renormalization',
        ],
      },
      {
        'id': 'entanglement',
        'title': "Quantum Entanglement",
        'tier': 'vip',
        'topics': [
          'Bell\'s theorem',
          'Quantum correlations',
          'Quantum information',
          'Quantum computing basics',
        ],
      },
    ],
    "Particle Physics (MSc)": [
      {
        'id': 'standard',
        'title': "Standard Model",
        'tier': 'free',
        'topics': [
          'Fundamental particles',
          'Force carriers',
          'Symmetry principles',
          'Standard Model predictions',
        ],
      },
      {
        'id': 'quarks',
        'title': "Quarks and Leptons",
        'tier': 'free',
        'topics': [
          'Quark properties',
          'Lepton characteristics',
          'Generation patterns',
          'Mixing phenomena',
        ],
      },
      {
        'id': 'detectors',
        'title': "Particle Detectors",
        'tier': 'vip',
        'topics': [
          'Detection principles',
          'Accelerator technology',
          'Data analysis',
          'Experimental techniques',
        ],
      },
    ],
    "Nuclear Physics (MSc)": [
      {
        'id': 'structure',
        'title': "Nuclear Structure",
        'tier': 'free',
        'topics': [
          'Nuclear models',
          'Shell model',
          'Collective model',
          'Nuclear structure calculations',
        ],
      },
      {
        'id': 'reactions',
        'title': "Nuclear Reactions",
        'tier': 'free',
        'topics': [
          'Reaction mechanisms',
          'Cross-section measurements',
          'Nuclear astrophysics',
          'Synthesis processes',
        ],
      },
      {
        'id': 'decay',
        'title': "Radioactive Decay",
        'tier': 'vip',
        'topics': [
          'Decay modes',
          'Half-life measurements',
          'Dating methods',
          'Medical applications',
        ],
      },
    ],
    "Astrophysics (MSc)": [
      {
        'id': 'stars',
        'title': "Stellar Evolution",
        'tier': 'free',
        'topics': [
          'Stellar formation',
          'Main sequence evolution',
          'Stellar death processes',
          'Supernova mechanisms',
        ],
      },
      {
        'id': 'cosmology',
        'title': "Cosmology",
        'tier': 'free',
        'topics': [
          'Cosmological models',
          'Dark matter evidence',
          'Dark energy properties',
          'Cosmic microwave background',
        ],
      },
      {
        'id': 'blackholes',
        'title': "Black Holes",
        'tier': 'vip',
        'topics': [
          'Event horizon',
          'Hawking radiation',
          'Accretion disks',
          'Gravitational waves',
        ],
      },
    ],
    
    "Condensed Matter (MSc)": [
      {
        'id': 'quantum',
        'title': "Quantum Materials",
        'tier': 'free',
        'topics': [
          'Topological insulators',
          'Quantum Hall effect',
          'Superconducting materials',
          'Novel quantum states',
        ],
      },
      {
        'id': 'superconductivity',
        'title': "Superconductivity",
        'tier': 'free',
        'topics': [
          'BCS theory details',
          'High-Tc mechanisms',
          'Superconducting applications',
          'Josephson junctions',
        ],
      },
      {
        'id': 'nanophysics',
        'title': "Nanophysics",
        'tier': 'vip',
        'topics': [
          'Quantum dots',
          'Nanowires',
          '2D materials',
          'Nanoscale phenomena',
        ],
      },
    ],
    "Recombinant DNA Technology (MSc)": [
      {
        'id': 'vectors',
        'title': "Advanced Vector Design",
        'tier': 'free',
        'topics': [
          'Vector design principles',
          'Expression optimization',
          'Synthetic biology',
          'Metabolic engineering',
        ],
      },
      {
        'id': 'expression',
        'title': "Gene Expression Systems",
        'tier': 'free',
        'topics': [
          'Promoter systems',
          'Inducible expression',
          'Secretion systems',
          'Protein targeting',
        ],
      },
      {
        'id': 'editing',
        'title': "Genome Editing",
        'tier': 'vip',
        'topics': [
          'Zinc finger nucleases',
          'TALEN technology',
          'CRISPR systems',
          'Therapeutic genome editing',
        ],
      },
    ],
    "Advanced Immunology (MSc)": [
      {
        'id': 'immunity',
        'title': "Advanced Immunity",
        'tier': 'free',
        'topics': [
          'Immune cell development',
          'Tolerance mechanisms',
          'Memory responses',
          'Vaccine immunology',
        ],
      },
      {
        'id': 'autoimmune',
        'title': "Autoimmune Diseases",
        'tier': 'free',
        'topics': [
          'Autoimmune pathogenesis',
          'Immunodeficiency diseases',
          'Hypersensitivity reactions',
          'Transplant immunology',
        ],
      },
      {
        'id': 'immunotherapy',
        'title': "Immunotherapy",
        'tier': 'vip',
        'topics': [
          'Cancer immunology',
          'Immunotherapy approaches',
          'Checkpoint inhibitors',
          'CAR-T cell therapy',
        ],
      },
    ],
    "Proteomics (MSc)": [
      {
        'id': 'proteome',
        'title': "Proteome Analysis",
        'tier': 'free',
        'topics': [
          'Protein separation',
          'Mass spectrometry',
          'Quantitative proteomics',
          'Post-translational modifications',
        ],
      },
      {
        'id': 'massspec',
        'title': "Mass Spectrometry",
        'tier': 'free',
        'topics': [
          'Instrumentation principles',
          'Data acquisition',
          'Spectral analysis',
          'Quantification methods',
        ],
      },
      {
        'id': 'interactions',
        'title': "Protein Interactions",
        'tier': 'vip',
        'topics': [
          'Yeast two-hybrid',
          'Co-immunoprecipitation',
          'Protein arrays',
          'Network analysis',
        ],
      },
    ],
    "Drug Design (MSc)": [
      {
        'id': 'design',
        'title': "Drug Design Principles",
        'tier': 'free',
        'topics': [
          'Target identification',
          'Lead discovery',
          'Structure-activity relationships',
          'Optimization strategies',
        ],
      },
      {
        'id': 'targets',
        'title': "Drug Targets",
        'tier': 'free',
        'topics': [
          'Receptor biology',
          'Enzyme inhibitors',
          'Ion channel modulators',
          'GPCR targeting',
        ],
      },
      {
        'id': 'delivery',
        'title': "Drug Delivery Systems",
        'tier': 'vip',
        'topics': [
          'ADME properties',
          'Toxicity assessment',
          'Formulation development',
          'Clinical trial design',
        ],
      },
    ],
    
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
    "NEET Preparation": [
      {
        'id': 'biology',
        'title': "NEET Biology",
        'tier': 'free',
        'topics': [
          'Human physiology systems',
          'Plant physiology mechanisms',
          'Reproduction biology',
          'Genetics and evolution concepts',
        ],
      },
      {
        'id': 'physics',
        'title': "NEET Physics",
        'tier': 'free',
        'topics': [
          'Human physiology details',
          'Digestive system',
          'Respiratory system',
          'Circulatory system',
          'Excretory system',
          'Nervous system',
          'Endocrine system',
        ],
      },
      {
        'id': 'chemistry',
        'title': "NEET Chemistry",
        'tier': 'vip',
        'topics': [
          'Photosynthesis',
          'Respiration in plants',
          'Plant growth regulators',
          'Mineral nutrition',
          'Transport in plants',
        ],
      },
    ],
    "JEE Main Preparation": [
      {
        'id': 'physics',
        'title': "JEE Main Physics",
        'tier': 'free',
        'topics': [
          'Mechanics problems',
          'Electromagnetism concepts',
          'Optics applications',
          'Modern physics topics',
        ],
      },
      {
        'id': 'chemistry',
        'title': "JEE Main Chemistry",
        'tier': 'free',
        'topics': [
          'Kinematics problems',
          'Dynamics applications',
          'Work-energy theorem',
          'Rotational motion',
          'Gravitation calculations',
        ],
      },
      {
        'id': 'math',
        'title': "JEE Main Mathematics",
        'tier': 'vip',
        'topics': [
          'Electrostatics problems',
          'Current electricity',
          'Magnetic effects',
          'EM induction',
          'AC circuits',
        ],
      },
    ],
    "JEE Advanced Preparation": [
      {
        'id': 'physics',
        'title': "JEE Advanced Physics",
        'tier': 'free',
        'topics': [
          'Advanced kinematics',
          'Rigid body dynamics',
          'Fluid mechanics',
          'Thermal physics advanced',
        ],
      },
      {
        'id': 'chemistry',
        'title': "JEE Advanced Chemistry",
        'tier': 'vip',
        'topics': [
          'Electrostatics advanced',
          'Magnetostatics complex',
          'EM theory applications',
          'Wave optics advanced',
        ],
      },
    ],
    "Science Olympiads": [
      {
        'id': 'junior',
        'title': "Junior Olympiad (Class 1-5)",
        'tier': 'free',
        'topics': [
          'Basic science concepts',
          'Logical reasoning',
          'Observation skills',
          'Scientific thinking',
        ],
      },
      {
        'id': 'senior',
        'title': "Senior Olympiad (Class 6-10)",
        'tier': 'free',
        'topics': [
          'Physics fundamentals',
          'Chemistry basics',
          'Biology principles',
          'Earth science concepts',
        ],
      },
      {
        'id': 'advanced',
        'title': "Advanced Olympiad (Class 11-12)",
        'tier': 'vip',
        'topics': [
          'Advanced problem solving',
          'Theoretical concepts',
          'Experimental design',
          'Scientific methodology',
        ],
      },
    ],
  
  };

}
