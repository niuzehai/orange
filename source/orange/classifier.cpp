/*
    This file is part of Orange.

    Orange is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    Orange is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with Orange; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

    Authors: Janez Demsar, Blaz Zupan, 1996--2002
    Contact: janez.demsar@fri.uni-lj.si
*/


#include "vars.hpp"
#include <math.h>
#include "errors.hpp"
#include "stladdon.hpp"
#include "random.hpp"
#include "examplegen.hpp"
#include "examples.hpp"
#include "domain.hpp"
//#include "filter.hpp"
#include "table.hpp"

#include "classify.ppp"

DEFINE_TOrangeVector_classDescription(PClassifier, "TClassifierList")

/* ***** TClassifier methods */

TClassifier::TClassifier(const PVariable &acv, const bool &cp)
: classVar(acv),
  computesProbabilities(cp)
{};


TClassifier::TClassifier(const bool &cp)
: classVar(PVariable()),
  computesProbabilities(cp)
{};


TClassifier::TClassifier(const TClassifier &old)
: TOrange(old),
  classVar(old.classVar),
  computesProbabilities(old.computesProbabilities)
{};


TValue TClassifier::operator ()(const TExample &exam)
{ if (!computesProbabilities)
    raiseError("invalid setting of 'computesProbabilities'");

  return classVar->varType==TValue::FLOATVAR ? TValue(classDistribution(exam)->average()) : classDistribution(exam)->highestProbValue(exam);
}    


PDistribution TClassifier::classDistribution(const TExample &exam)
{ if (computesProbabilities) 
    raiseError("invalid setting of 'computesProbabilities'");

  PDistribution dist = TDistribution::create(classVar);
  dist->add(operator()(exam));
  return dist;
}

void TClassifier::predictionAndDistribution(const TExample &ex, TValue &val, PDistribution &classDist)
{ if (computesProbabilities) {
    classDist = classDistribution(ex);
    val = classVar->varType==TValue::FLOATVAR ? TValue(classDist->average()) : classDist->highestProbValue(ex);
  }
  else {
    val = operator()(ex);
    classDist = TDistribution::create(classVar);
    classDist->add(val);
  }
}



class TExampleForMissing : public TExample {
public:
  PEFMDataDescription dataDescription; //P data description
  vector<int> DKs;
  vector<int> DCs;

  TExampleForMissing(PDomain, PEFMDataDescription = PEFMDataDescription());
  TExampleForMissing(const TExample &orig, PEFMDataDescription =PEFMDataDescription());
  TExampleForMissing(const TExampleForMissing &orig);
  TExampleForMissing(PDomain dom, const TExample &orig, PEFMDataDescription);

  virtual TExampleForMissing &operator =(const TExampleForMissing &orig);
  virtual TExample &operator =(const TExample &orig);

  void resetExample();
  bool nextExample();
  bool hasMissing();
};


TEFMDataDescription::TEFMDataDescription(PDomain dom, PDomainDistributions dist, int ow, int mw)
: domain(dom),
  domainDistributions(dist),
  originalWeight(ow),
  missingWeight(mw)
{ getAverages();}


void TEFMDataDescription::getAverages()
{ averages = vector<float>();
  if (domainDistributions)
    for(TDomainDistributions::iterator si(domainDistributions->begin()), ei(domainDistributions->end()); si!=ei; si++)
      averages.push_back(((*si)->variable->varType==TValue::INTVAR)
                          ? numeric_limits<float>::quiet_NaN()
                          : (*si)->average());
}


TExampleForMissing::TExampleForMissing(PDomain dom, PEFMDataDescription dd)
: TExample(dom),
  dataDescription(dd)
{ if (dd && (dd->domain!=domain))
    raiseError("data description does not match the domain");
}


TExampleForMissing::TExampleForMissing(const TExampleForMissing &orig)
: TExample((const TExample &)(orig)),
  dataDescription(orig.dataDescription),
  DKs(orig.DKs),
  DCs(orig.DCs)
{}


TExampleForMissing::TExampleForMissing(const TExample &orig, PEFMDataDescription dd)
: TExample(orig),
  dataDescription(dd)
{ if (dd && (dd->domain!=domain))
    raiseError("data description does not match the domain");
}


TExampleForMissing::TExampleForMissing(PDomain dom, const TExample &orig, PEFMDataDescription dd)
: TExample(dom, orig),
  dataDescription(dd)
{ if (dd && (dd->domain!=domain))
    raiseError("data description does not match the domain");
}


TExampleForMissing &TExampleForMissing::operator =(const TExampleForMissing &orig)
{ (TExample &)(*this) = (const TExample &)(orig);
  dataDescription=orig.dataDescription;
  DKs = orig.DKs;
  DCs = orig.DCs;
  return *this;
}

TExample &TExampleForMissing::operator =(const TExample &orig)
{ (TExample &)(*this).TExample::operator=(orig);
  return *this;
}


void TExampleForMissing::resetExample()
{ 
  checkProperty(dataDescription);

  DCs.clear();
  DKs.clear();

  float averageWeight=1;

  TVarList::const_iterator vi(domain->attributes->begin()), vie(domain->attributes->end());
  TExample::iterator ei(begin()), bei(ei);
  vector<float>::const_iterator ai(dataDescription->averages.begin());
  for(; vi!=vie; ei++, vi++, ai++)
    if ((*ei).isSpecial()) {
      if ((*ei).varType==TValue::FLOATVAR)
        *ei=TValue(*ai);
      else if (dataDescription->missingWeight && (*ei).isDK()) {
        DKs.push_back(ei-bei);
        averageWeight/=float((*vi)->noOfValues());
      }
      else
        DCs.push_back(ei-bei);

      (*vi)->firstValue(*ei);
    }

  if (dataDescription->missingWeight) {
    float weight = dataDescription->originalWeight ? getMeta(dataDescription->originalWeight).floatV : 1;
    if (dataDescription->domainDistributions) {
      TDomainDistributions::const_iterator di(dataDescription->domainDistributions->begin());
      ITERATE(vector<int>, ci, DKs) {
        // DKs contain only discrete variables, so it is safe to cast
        const TDiscDistribution &dist = CAST_TO_DISCDISTRIBUTION(*(di+*ci));
        weight *= dist.front() / dist.abs;
      }
    }
    else
      weight=weight*averageWeight;

    setMeta(dataDescription->missingWeight, TValue(weight));
  }
}


bool TExampleForMissing::nextExample()
{
  TVarList::const_iterator vi(domain->variables->begin());
  vector<int>::iterator ci, ei;

  // first DCs since they don't change weights. If one is increased, job is done and we return true
  for(ci=DCs.begin(), ei=DCs.end(); ci!=ei; ci++)
    if ((*(vi+*ci))->nextValue(operator[](*ci)))
      return true;
    else
      (*(vi+*ci))->firstValue(operator[](*ci));

  // if DCs or all exhausted, increase DKs
  for(ci=DKs.begin(), ei=DKs.end(); (ci!=ei) && !(*(vi+*ci))->nextValue(operator[](*ci)); ci++)
    (*(vi+*ci))->firstValue(operator[](*ci));

  if (ci==ei)
    return false;

  if (dataDescription->missingWeight && dataDescription->domainDistributions) {
    float weight=dataDescription->originalWeight ? getMeta(dataDescription->originalWeight).floatV : 1;
    if (dataDescription->domainDistributions) {
      TDomainDistributions::const_iterator di(dataDescription->domainDistributions->begin());
      ITERATE(vector<int>, ci, DKs) {
        // DKs contain only discrete variables, so it is safe to cast
        const TDiscDistribution &dist = CAST_TO_DISCDISTRIBUTION(*(di+*ci));
        weight*= dist[operator[](*ci).intV] / dist.abs;
      }
    }
    setMeta(dataDescription->missingWeight, TValue(weight));
  }

  return true;
}

bool TExampleForMissing::hasMissing() 
{ return DCs.size() || DKs.size(); }

/*  This method can be called by derived classes when example misses values and missed
    values are not tolerated by the model.
    Provided the data description for missing values it constructs the TExampleForMissing,
    calls the operator()(const TExample &) and returns the majority class of the weighted
    class distributions. */
TValue TClassifier::operator ()(const TExample &example, PEFMDataDescription dataDes)
{ if (classVar->varType==TValue::FLOATVAR)
    raiseError("classification with missing values imputation works only for discrete classes.");
  checkProperty(dataDes);

  TExampleForMissing exMissing(example, dataDes);
  exMissing.resetExample();
  TDiscDistribution classDist;
  do {
    TValue cv = operator()(exMissing);
    if (!cv.isSpecial())
      classDist.addint(cv.intV, dataDes->missingWeight ? float(exMissing[dataDes->missingWeight]) : 1.0);
  } while (exMissing.nextExample());

  return classDist.highestProbValue(example);
}

/*  This method can be called by derived classes when example misses values and missed
    values are not tolerated by the model.
    Provided the data description for missing values it constructs the TExampleForMissing,
    calls the classDistribution(const TExample &) and returns the weighted class distributions. */
PDistribution TClassifier::classDistribution(const TExample &example, PEFMDataDescription dataDes)
{
  TExampleForMissing exMissing(example, dataDes);
  exMissing.resetExample();
  TDistribution *classDist = TDistribution::create(classVar);
  PDistribution res = classDist;

  do
    if (dataDes->missingWeight)
      classDist->operator += ((classDistribution(exMissing)->operator *= (exMissing[dataDes->missingWeight])));
    else 
      classDist->operator += (classDistribution(exMissing).getReference());
  while (exMissing.nextExample());
 
  return res;
}



TClassifierFD::TClassifierFD(const bool &cp)
: TClassifier(cp)
{}


TClassifierFD::TClassifierFD(PDomain dom, const bool &cp)
: TClassifier(dom ? dom->classVar : PVariable(), cp),
  domain(dom)
{}
  

TClassifierFD::TClassifierFD(const TClassifierFD &old)
: TClassifier(old),
  domain(old.domain)
{}


void TClassifierFD::afterSet(const string &name)
{ if (name=="domain")
    classVar=domain->classVar;
}




TDefaultClassifier::TDefaultClassifier()
: TClassifier(true)
{}


TDefaultClassifier::TDefaultClassifier(PVariable acv) 
: TClassifier(acv, true),
  defaultVal(acv ? acv->DK() : TValue()), 
  defaultDistribution(TDistribution::create(acv))
{}


TDefaultClassifier::TDefaultClassifier(PVariable acv, PDistribution defDis)
: TClassifier(acv, true),
  defaultVal(),
  defaultDistribution(defDis)
{}


TDefaultClassifier::TDefaultClassifier(PVariable acv, const TValue &defVal, PDistribution defDis)
: TClassifier(acv, true),
  defaultVal(defVal),
  defaultDistribution(defDis)
{}


TDefaultClassifier::TDefaultClassifier(const TDefaultClassifier &old)
: TClassifier(dynamic_cast<const TClassifier &>(old)),
  defaultVal(old.defaultVal), 
  defaultDistribution(CLONE(TDistribution, old.defaultDistribution))
{}


TValue TDefaultClassifier::operator ()(const TExample &exam)
{ if (defaultVal.isSpecial())
    return defaultDistribution->supportsContinuous ? TValue(defaultDistribution->average()) : defaultDistribution->highestProbValue(exam);

  return defaultVal;
}


PDistribution TDefaultClassifier::classDistribution(const TExample &)
{ return CLONE(TDistribution, defaultDistribution); }


void TDefaultClassifier::predictionAndDistribution(const TExample &exam, TValue &val, PDistribution &dist)
{ if (defaultVal.isSpecial())
    val = defaultDistribution->supportsContinuous ? TValue(defaultDistribution->average()) : defaultDistribution->highestProbValue(exam);
  else
    val = defaultVal;

  dist = CLONE(TDistribution, defaultDistribution);
}




TRandomClassifier::TRandomClassifier(PVariable acv)
: TClassifier(acv)
{
  if (classVar->varType != TValue::INTVAR)
    raiseError("discrete class expected (which '%s' is not)", classVar->name.c_str());

  probabilities = dynamic_cast<TDiscDistribution *>(TDistribution::create(acv));
  if (probabilities)
    // if distribution is discrete, it sets probabilities to 1/acv->noOfValues
    probabilities->normalize();
}


TRandomClassifier::TRandomClassifier(const TDiscDistribution &probs)
: TClassifier(),
  probabilities(mlnew TDiscDistribution(probs))
{ probabilities->normalize(); }


TRandomClassifier::TRandomClassifier(PVariable acv, const TDiscDistribution &probs)
: TClassifier(acv), probabilities(mlnew TDiscDistribution(probs))
{ probabilities->normalize(); }


TRandomClassifier::TRandomClassifier(PDiscDistribution probs)
  : TClassifier(), probabilities(probs)
  { probabilities->normalize(); }


TRandomClassifier::TRandomClassifier(PVariable acv, PDiscDistribution probs)
  : TClassifier(acv), probabilities(probs)
  { probabilities->normalize(); }


TValue TRandomClassifier::operator()(const TExample &)
{ return probabilities->randomValue(); }


PDistribution TRandomClassifier::classDistribution(const TExample &)
{ return CLONE(TDistribution, probabilities); }

     
void TRandomClassifier::predictionAndDistribution(const TExample &, TValue &val, PDistribution &dist)
{ val = probabilities->randomValue();
  dist = CLONE(TDistribution, probabilities);
}
