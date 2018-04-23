class WikipediaKnowledge:
    @staticmethod
    def all_wikipedia_language_codes_order_by_importance():
        # list from https://meta.wikimedia.org/wiki/List_of_Wikipedias as of 2017-10-07
        # ordered by article count except some for extreme bot spam
        return ['en', 'de', 'fr', 'nl', 'ru', 'it', 'es', 'pl',
                'vi', 'ja', 'pt', 'zh', 'uk', 'fa', 'ca', 'ar', 'no', 'sh', 'fi',
                'hu', 'id', 'ko', 'cs', 'ro', 'sr', 'ms', 'tr', 'eu', 'eo', 'bg',
                'hy', 'da', 'zh-min-nan', 'sk', 'min', 'kk', 'he', 'lt', 'hr',
                'ce', 'et', 'sl', 'be', 'gl', 'el', 'nn', 'uz', 'simple', 'la',
                'az', 'ur', 'hi', 'vo', 'th', 'ka', 'ta', 'cy', 'mk', 'mg', 'oc',
                'tl', 'ky', 'lv', 'bs', 'tt', 'new', 'sq', 'tg', 'te', 'pms',
                'br', 'be-tarask', 'zh-yue', 'bn', 'ml', 'ht', 'ast', 'lb', 'jv',
                'mr', 'azb', 'af', 'sco', 'pnb', 'ga', 'is', 'cv', 'ba', 'fy',
                'su', 'sw', 'my', 'lmo', 'an', 'yo', 'ne', 'gu', 'io', 'pa',
                'nds', 'scn', 'bpy', 'als', 'bar', 'ku', 'kn', 'ia', 'qu', 'ckb',
                'mn', 'arz', 'bat-smg', 'wa', 'gd', 'nap', 'bug', 'yi', 'am',
                'si', 'cdo', 'map-bms', 'or', 'fo', 'mzn', 'hsb', 'xmf', 'li',
                'mai', 'sah', 'sa', 'vec', 'ilo', 'os', 'mrj', 'hif', 'mhr', 'bh',
                'roa-tara', 'eml', 'diq', 'pam', 'ps', 'sd', 'hak', 'nso', 'se',
                'ace', 'bcl', 'mi', 'nah', 'zh-classical', 'nds-nl', 'szl', 'gan',
                'vls', 'rue', 'wuu', 'bo', 'glk', 'vep', 'sc', 'fiu-vro', 'frr',
                'co', 'crh', 'km', 'lrc', 'tk', 'kv', 'csb', 'so', 'gv', 'as',
                'lad', 'zea', 'ay', 'udm', 'myv', 'lez', 'kw', 'stq', 'ie',
                'nrm', 'nv', 'pcd', 'mwl', 'rm', 'koi', 'gom', 'ug', 'lij', 'ab',
                'gn', 'mt', 'fur', 'dsb', 'cbk-zam', 'dv', 'ang', 'ln', 'ext',
                'kab', 'sn', 'ksh', 'lo', 'gag', 'frp', 'pag', 'pi', 'olo', 'av',
                'dty', 'xal', 'pfl', 'krc', 'haw', 'bxr', 'kaa', 'pap', 'rw',
                'pdc', 'bjn', 'to', 'nov', 'kl', 'arc', 'jam', 'kbd', 'ha', 'tpi',
                'tyv', 'tet', 'ig', 'ki', 'na', 'lbe', 'roa-rup', 'jbo', 'ty',
                'mdf', 'kg', 'za', 'wo', 'lg', 'bi', 'srn', 'zu', 'chr', 'tcy',
                'ltg', 'sm', 'om', 'xh', 'tn', 'pih', 'chy', 'rmy', 'tw', 'cu',
                'kbp', 'tum', 'ts', 'st', 'got', 'rn', 'pnt', 'ss', 'fj', 'bm',
                'ch', 'ady', 'iu', 'mo', 'ny', 'ee', 'ks', 'ak', 'ik', 've', 'sg',
                'dz', 'ff', 'ti', 'cr', 'atj', 'din', 'ng', 'cho', 'kj', 'mh',
                'ho', 'ii', 'aa', 'mus', 'hz', 'kr',
                # degraded due to major low-quality bot spam
                'ceb', 'sv', 'war'
                ]
