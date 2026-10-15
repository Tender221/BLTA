"""BLTA on frozen encoder features. Tool identities must come from the executor."""
from __future__ import annotations
import numpy as np


class BLTA:
    """Linear guard on frozen features with trusted benign-log tool offsets.

    Tool identities are supplied by the executor. Unknown identities use the
    unchanged source score. An infinite threshold is the valid conservative
    quantile result when too few calibration observations are available.
    """
    def __init__(self, mean, scale, weight, bias, threshold, offsets=None):
        self.mean = np.asarray(mean, dtype=np.float64)
        self.scale = np.asarray(scale, dtype=np.float64)
        self.weight = np.asarray(weight, dtype=np.float64)
        if (self.mean.ndim != 1 or not len(self.mean) or self.scale.shape != self.mean.shape
                or self.weight.shape != self.mean.shape
                or not np.isfinite([self.mean, self.scale, self.weight]).all()
                or np.any(self.scale <= 0)):
            raise ValueError('Need aligned finite mean, positive scale and weight vectors')
        self.bias = float(bias)
        self.threshold = float(threshold)
        self.offsets = {str(tool): float(offset) for tool, offset in (offsets or {}).items()}
        if (not np.isfinite(self.bias) or np.isnan(self.threshold)
                or not np.isfinite(list(self.offsets.values())).all()):
            raise ValueError('Need finite bias and offsets, and a non-NaN threshold')

    @classmethod
    def from_dict(cls, record):
        return cls(**record)

    @classmethod
    def fit(cls, source_normal, source_attack, calibration_normal, alpha=.01, l2=.01):
        """Fit balanced ridge and calibrate on separate source-benign features."""
        from scipy.linalg import cho_factor, cho_solve
        normal = np.asarray(source_normal, dtype=np.float64)
        attack = np.asarray(source_attack, dtype=np.float64)
        calibration = np.asarray(calibration_normal, dtype=np.float64)
        arrays = [normal, attack, calibration]
        if (any(a.ndim != 2 or not len(a) or not np.isfinite(a).all() for a in arrays)
                or len({a.shape[1] for a in arrays}) != 1
                or not 0 < alpha < 1 or not l2 > 0):
            raise ValueError('Need finite source fitting classes, separate benign calibration and positive L2')
        mean, scale = normal.mean(axis=0), normal.std(axis=0)
        scale = np.where(scale > 1e-12, scale, 1.)
        x = (np.concatenate([normal, attack])-mean)/scale
        mass = np.r_[np.full(len(normal), .5/len(normal)), np.full(len(attack), .5/len(attack))]
        targets = np.r_[-np.ones(len(normal)), np.ones(len(attack))]
        center, target_mean = mass@x, float(mass@targets)
        centered = x-center
        covariance = centered.T@(mass[:,None]*centered)
        weight = cho_solve(cho_factor(covariance+l2*np.eye(x.shape[1]), lower=True),
                           centered.T@(mass*(targets-target_mean)))
        head = cls(mean,scale,weight,target_mean-center@weight,np.inf)
        scores = np.sort(head.scores(calibration))
        rank = int(np.ceil((len(scores)+1)*(1-alpha)))
        head.threshold = float(scores[rank-1]) if rank <= len(scores) else np.inf
        return head

    def scores(self, features, tools=None):
        """Score an (observations, features) matrix with optional per-row tool IDs."""
        vectors = np.asarray(features, dtype=np.float64)
        if (vectors.ndim != 2 or vectors.shape[1] != len(self.weight)
                or not np.isfinite(vectors).all()):
            raise ValueError('Need a finite feature matrix with the encoder dimension')
        scores = ((vectors-self.mean)/self.scale) @ self.weight + self.bias
        if tools is not None:
            if isinstance(tools, (str, bytes)) or len(tools) != len(vectors):
                raise ValueError('One executor-assigned tool identity per observation is required')
            scores += np.array([self.offsets.get(str(tool), 0.) for tool in tools])
        return scores

    def adapt(self, tool, target_normal):
        """Store one offset from trusted target-normal features; keep source fixed."""
        normals = np.asarray(target_normal, dtype=np.float64)
        if normals.ndim != 2 or not len(normals):
            raise ValueError('Onboarding requires trusted target-normal features')
        # Evaluate the mean feature with the unchanged source head. This avoids
        # a large batch forward through the linear readout during onboarding.
        self.offsets[str(tool)] = self.bias-float(self.scores(normals.mean(axis=0,keepdims=True))[0])
        return self.offsets[str(tool)]

    def blocked(self, features, tools=None):
        """Return True exactly when the adapted score exceeds the source threshold."""
        return self.scores(features, tools) > self.threshold

    def to_dict(self):
        return dict(mean=self.mean.tolist(), scale=self.scale.tolist(),
                    weight=self.weight.tolist(), bias=self.bias,
                    threshold=self.threshold, offsets=self.offsets.copy())
