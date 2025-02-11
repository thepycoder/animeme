import bisect
import copy
from abc import abstractmethod, ABC
from typing import Tuple, Optional, List, Union

import numpy as np


class Keyframe(ABC):
    __slots__ = 'frame_ind',

    def copy(self):
        return copy.deepcopy(self)

    @abstractmethod
    def update_keyframe(self, new_keyframe: 'Keyframe'):
        raise NotImplementedError

    def __init__(self, frame_ind: int):
        self.frame_ind = frame_ind

    def __lt__(self, other: 'Keyframe'):
        return self.frame_ind < other.frame_ind

    def __repr__(self):
        return f'{self.__class__.__name__}(frame_ind={self.frame_ind})'


class KeyframeCollection(ABC):
    def __init__(self):
        self._keyframes = []

    def insert_keyframe(self, keyframe: Keyframe):
        insertion_index = bisect.bisect_left(self._keyframes, keyframe)

        if self._keyframes:
            if not keyframe.text_size:
                keyframe.text_size = self._keyframes[max(0, insertion_index - 1)].text_size
        else:
            keyframe.text_size = TextAnimationKeyframeCollection.DEFAULT_TEXT_SIZE

        if insertion_index < len(self) and keyframe.frame_ind == self._keyframes[insertion_index].frame_ind:
            self._keyframes[insertion_index].update_keyframe(new_keyframe=keyframe)
        else:
            self._keyframes.insert(insertion_index, keyframe)

    def remove_keyframe(self, frame_ind: int):
        index = self.keyframes_frames_indices.index(frame_ind)
        self._keyframes.pop(index)

    def get_keyframe(self, frame_ind: int):
        return self._keyframes[self.keyframes_frames_indices.index(frame_ind)]

    @property
    def keyframes_frames_indices(self):
        return [keyframe.frame_ind for keyframe in self._keyframes]

    def reset(self):
        self._keyframes = []

    def __getitem__(self, item) -> Keyframe:
        return self._keyframes[item]

    def __len__(self):
        return len(self._keyframes)

    def __repr__(self):
        return f'{self.__class__.__name__}({self._keyframes})'


class TextAnimationKeyframeCollection(KeyframeCollection):
    DEFAULT_POSITION = (20, 20)
    DEFAULT_TEXT_SIZE = 50

    def __getitem__(self, item) -> Union['TextAnimationKeyframe', List['TextAnimationKeyframe']]:
        return self._keyframes[item]

    def interpolate(self, frame_ind: int) -> 'TextAnimationKeyframe':
        all_position_x = [(keyframe.frame_ind, keyframe.x) for keyframe in self if keyframe.x is not None]
        all_position_y = [(keyframe.frame_ind, keyframe.y) for keyframe in self if keyframe.y is not None]
        all_text_size = [(keyframe.frame_ind, keyframe.text_size)
                         for keyframe in self if keyframe.text_size is not None]

        assert len(all_position_x) == len(all_position_y)

        if all_position_x:
            interp_x = int(np.interp(frame_ind, *zip(*all_position_x)))
            interp_y = int(np.interp(frame_ind, *zip(*all_position_y)))
        else:
            interp_x, interp_y = self.DEFAULT_POSITION

        if all_text_size:
            interp_text_size = int(np.interp(frame_ind, *zip(*all_text_size)))
        else:
            interp_text_size = self.DEFAULT_TEXT_SIZE

        return TextAnimationKeyframe(frame_ind=frame_ind,
                                     position=(interp_x, interp_y),
                                     text_size=interp_text_size)

    def serialize(self) -> List[dict]:
        return [keyframe.serialize() for keyframe in self]

    @classmethod
    def deserialize(cls, list_of_keyframes) -> 'TextAnimationKeyframeCollection':
        collection = cls()
        for keyframe_dict in list_of_keyframes:
            collection.insert_keyframe(TextAnimationKeyframe.deserialize(keyframe_dict))
        return collection


class TextAnimationKeyframe(Keyframe):
    def __init__(self, frame_ind: int, position: Optional[Tuple[int, int]] = None, text_size=None):
        super().__init__(frame_ind)
        if position is not None:
            self.x, self.y = position
        else:
            self.x = self.y = None
        self.text_size = text_size

    def update_keyframe(self, new_keyframe: 'TextAnimationKeyframe'):
        if new_keyframe.position is not None:
            self.position = new_keyframe.position
        if new_keyframe.text_size is not None:
            self.text_size = new_keyframe.text_size

    @property
    def position(self):
        return self.x, self.y

    @position.setter
    def position(self, new_position: Tuple[int, int]):
        self.x, self.y = new_position

    def serialize(self) -> dict:
        return dict(frame_ind=self.frame_ind, position=self.position, text_size=self.text_size)

    @classmethod
    def deserialize(cls, serialized_dict: dict) -> 'TextAnimationKeyframe':
        return cls(frame_ind=serialized_dict['frame_ind'],
                   position=serialized_dict['position'],
                   text_size=serialized_dict['text_size'])

    def __eq__(self, other: 'TextAnimationKeyframe'):
        return self.frame_ind == other.frame_ind and \
               self.position == other.position and \
               self.text_size == other.text_size

    def __repr__(self):
        return f'{self.__class__.__name__}' \
               f'(frame_ind={self.frame_ind}, ' \
               f'position={self.position}, ' \
               f'text_size={self.text_size})'


if __name__ == '__main__':
    def show_keyframes_timeline(collection: TextAnimationKeyframeCollection, length=50):
        timeline = ""
        keyframes_indices = collection.keyframes_frames_indices
        for frame_ind in range(length):
            if frame_ind in keyframes_indices:
                timeline += "◆"
            else:
                timeline += "-"
        print(timeline)

    a = TextAnimationKeyframe(frame_ind=8, position=(50, 60))
    b = TextAnimationKeyframe(frame_ind=2, position=(0, 0), text_size=20)
    c = TextAnimationKeyframe(frame_ind=4, position=(20, 30))
    keyframe_collection = TextAnimationKeyframeCollection()
    keyframe_collection.insert_keyframe(a)
    print(keyframe_collection)
    keyframe_collection.insert_keyframe(b)
    print(keyframe_collection)
    keyframe_collection.insert_keyframe(c)
    print(keyframe_collection)

    keyframe_collection.insert_keyframe(keyframe_collection.interpolate(49))
    print(keyframe_collection)

    show_keyframes_timeline(keyframe_collection)
