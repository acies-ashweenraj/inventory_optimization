import re


def data_processing(df,style='camel'):
    
    def clean_name(col):
        # Remove special characters
        col = re.sub(r'[^\w\s]', '', col)
        # Replace whitespace with underscore
        col = col.strip().replace(' ', '_')
        if style == 'camel':
            parts = col.lower().split('_')
            return parts[0] + ''.join(word.capitalize() for word in parts[1:])
        else:  # default to snake_case
            return col.lower()
    
    df.columns = [clean_name(col) for col in df.columns]
    return df