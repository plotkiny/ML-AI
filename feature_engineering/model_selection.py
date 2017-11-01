#!usr/bin/env/python

import warnings
from sklearn.model_selection import StratifiedShuffleSplit
from gensim.models.word2vec import LineSentence
from gensim.corpora import Dictionary
from gensim.models.ldamulticore import LdaMulticore
from feature_engineering.loading_data import saveData
from feature_engineering.nlp_methods import sentencePunctuationParser
from feature_engineering.nlp_methods import sentenceStopWordsRemoval


def stratifiedSplit(df, response_var, n_splits=2, test_size=.15, random_state=22):

    """
    Splitting data into training and test sets.
    """

    split = StratifiedShuffleSplit(n_splits=n_splits, test_size=test_size, random_state=random_state)
    for train_index, test_index in split.split(df, response_var):
        X_train, X_test = df.loc[train_index], df.loc[test_index]
        y_train, y_test = response_var[train_index], response_var[test_index]

    return X_train, y_train, X_test, y_test


class lda_TopicModeling():

    """
    LDA Modeling using the Gensim python package. Incorporated methods for creating the model, saving and loading
    functionality.
    """

    def __init__(self, df):
        self.df = df

    def processTrainingData(self, file_path, training_data = None):

        """
        Remove punctuation, whitespace and stopwords from each review
        Output of 'sentencePunctuationParser' is a list of tokens if False, string if True
        Output of 'sentenceStopWordsRemoval' is a list of tokens if False, string if True
        """
        if training_data: #data is loaded via an input argument or when class is instantiated
            self.df = training_data

        processed_training_data = self.df.apply(lambda r: sentenceStopWordsRemoval(sentencePunctuationParser(r), True))
        for review in processed_training_data:
            saveData(review, file_path)

    def loadLineSentence(self, file_path):

        """
        Method to load the  reviews using Gensim's LineSentence.
        """
        return LineSentence(file_path)

    def createDictionary(self, review):

        """
        Create the LDA dictionary.
        """
        self.dictionary = Dictionary(review)


        return self.dictionary

    def filterDictionary(self,no_below,no_above):

        """
        Method for filtering very rare or too common from the dictionary (filter_extremes) and reassign
        integer ids (compactify).
        """
        self.dictionary.filter_extremes(no_below=10, no_above=0.4)
        self.dictionary.compactify()

    def saveDictionary(self, file_path):

        """
        Method for saving dictionary
        """
        self.dictionary.save(file_path)


    def unigramBowGenerator(self, file_path):

        """
        generator function to read reviews from a file
        and yield a bag-of-words representation
        """
        for review in LineSentence(file_path):
            yield self.dictionary.doc2bow(review)

    def createLDAModel(self, bow_corpus, topics, workers):

        """
        Method for creating the LDA model
        """
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')

            # workers => sets the parallelism, and should be set to your number of physical cores minus one
            self.lda = LdaMulticore(bow_corpus,
                                    num_topics=topics,  #12 topics for the 12 unique users
                                    id2word=self.dictionary,
                                    workers=workers)
            return self.lda

    def saveModel(self, file_path):

        """
        Method for saving LDA model to file
        """
        self.lda.save(file_path)

    def explore_topic(self, topic_number, lda = None, topn=10):

        """
        Method for accepting a user-supplied topic number and print out a formatted list of the top terms.
        """
        if not lda:
            self.lda = lda

        print ('{:20} {}'.format('term', 'frequency') + u'\n')

        for term, frequency in self.lda.show_topic(topic_number, topn=10):
            print('{:20} {:.3f}'.format(term, round(frequency, 3)))

    def assignTopic(self, processed_review, topics_returned = 1, min_top_freq = .05 ):

        """
        Assign topics to new reviews/documents using the trained model.
        """
        review_bow = self.dictionary.doc2bow(processed_review) #bag of words representation
        review_lda = self.lda[review_bow] #making a lda representation
        review_lda = sorted(review_lda,key=lambda t:( t[0], -t[1]))
        return review_lda[:topics_returned] if topics_returned < len(review_lda) else review_lda


