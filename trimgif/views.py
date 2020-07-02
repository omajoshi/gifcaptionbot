from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings

from .models import Movie

import os
import string
import srt

from datetime import datetime
from moviepy.editor import *

def check_match(query, sub):
    return query.lower().translate(str.maketrans('', '', string.punctuation)) in sub.content.lower().translate(str.maketrans('', '', string.punctuation))

def create(request):
    if request.method == "GET" or not (start_ind:=request.POST.get("start", None)) or not (end_ind:=request.POST.get("end", None)) or not (movie_id:=request.POST.get("movie", None)):
        return redirect('trimgif:search')
    movie = get_object_or_404(Movie, id=movie_id)
    with VideoFileClip(os.path.join(settings.BASE_DIR, movie.movie.name)) as clip:
        filepath = os.path.join(settings.BASE_DIR, movie.srt.name)
        with open(filepath, 'r') as f:
            subs = list(srt.parse(f.read()))
            start, end = subs[int(start_ind)-1], subs[int(end_ind)-1]
        clip = clip.subclip(str(start.start), str(end.end)).resize(.5)
        gif = f'media/gifs/gif_{datetime.now().strftime("%Y%m%d_%H%M%S")}.gif'
        clip.write_gif(os.path.join(settings.BASE_DIR, gif))
    return redirect('/'+gif)

def search(request):
    results = []
    if request.method == "GET" and (query:=request.GET.get("query", None)):
        for movie in Movie.objects.all():
            filepath = os.path.join(settings.BASE_DIR, movie.srt.name)
            with open(filepath, 'r') as f:
                subs = list(srt.parse(f.read()))
                param = 2
                delta = 15
                first_pass = []
                for i, sub in enumerate(subs):
                    if check_match(query, sub):
                        for x in range(i-param, i):
                            if x > -1 and (subs[i].start-subs[x].end).seconds < delta:
                                first_pass.append(subs[x])
                        first_pass.append(subs[i])
                        for x in range(i, i+param+1):
                            if x < len(subs) and (subs[x].start-subs[i].end).seconds < delta:
                                first_pass.append(subs[x])
                            else:
                                continue
                if not first_pass:
                    continue
                lines = [first_pass[0]]
                for line in first_pass[1:]:
                    if line.index > lines[-1].index:
                        lines.append(line)
                quote = {'data': [lines[0]], 'movie': movie.id}
                prev = lines[0]
                for line in lines[1:]:
                    if line.index - prev.index > 1:
                        quote['start'] = quote['data'][0].index
                        quote['end'] = quote['data'][-1].index
                        results.append(quote)
                        quote = {'data': [], 'movie': movie.id}
                    quote['data'].append(line)
                    prev = line
                quote['start'] = quote['data'][0].index
                quote['end'] = quote['data'][-1].index
                results.append(quote)
    return render(request, 'trimgif/search.html', {'results': results})
