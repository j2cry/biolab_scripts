import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns


dataset = pd.read_csv('dataset.csv', index_col=None, sep=';', encoding='utf-8')

plt.rc('xtick', labelsize=8)    # fontsize of the tick labels
plt.rc('ytick', labelsize=8)    # fontsize of the tick labels

# prepare data


# print(dataset.info())
# print(dataset.describe())

# Estimate distribution
estimate_counts = dataset['estimate'].value_counts(normalize=True)
# sns.countplot(dataset['estimate'])
sns.barplot(estimate_counts.index, estimate_counts)
plt.title('Общее распределение оценок')
plt.xlabel('Оценка')
plt.ylabel('')
plt.savefig('estimate.svg', format='svg')
plt.show()

# exit(0)
# RIN distribution
sns.kdeplot(dataset['RIN'], fill=True)
plt.title('Общее распределение RIN')
plt.xlabel('RIN')
plt.ylabel('')
plt.savefig('rin.svg', format='svg')
plt.show()

# распределение по поставщикам
out_provider = dataset['provider'].isna()
dataset.drop(dataset[out_provider].index, inplace=True)

# средние оценки по поставщикам
plt.figure(figsize=(12, 8))
df = dataset[['provider', 'estimate']].groupby(['provider'], as_index=False).agg('mean').rename(columns={'estimate': 'mean_estimate'})
sns.barplot(df['mean_estimate'], df['provider'], orient='h')
plt.title('Средняя оценка по поставщикам')
plt.xlabel('Средняя оценка')
plt.ylabel('')
plt.savefig('mean_estimate.svg', format='svg')
plt.show()

# средний RIN по поставщикам
plt.figure(figsize=(12, 8))
df = dataset[['provider', 'RIN']].groupby(['provider'], as_index=False).agg('mean').rename(columns={'RIN': 'mean_RIN'})
sns.barplot(df['mean_RIN'], df['provider'], orient='h')
plt.title('Средний RIN по поставщикам')
plt.xlabel('Средний RIN')
plt.ylabel('')
plt.savefig('mean_rin.svg', format='svg')
plt.show()

