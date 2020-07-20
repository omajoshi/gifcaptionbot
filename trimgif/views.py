from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings

from django.http import HttpResponse, JsonResponse

from .models import Movie

import os
import string
import srt

from celery import shared_task
# from celery.result import AsyncResult
from datetime import datetime
from moviepy.editor import concatenate_videoclips, VideoFileClip, CompositeVideoClip, TextClip

def check_match(query, sub):
    q = query.lower().translate(str.maketrans('', '', string.punctuation))
    s = sub.content.lower().translate(str.maketrans('', '', string.punctuation))
    return q in s or s in q

def retrieve_before_lines(request):
    pass

def retrieve_after_lines(request):
    pass

def edit(request):
    if not (start_ind:=request.GET.get("start", None)) or not (end_ind:=request.GET.get("end", None)) or not (movie_id:=request.GET.get("movie", None)):
        return redirect('trimgif:search')
    movie = get_object_or_404(Movie, id=movie_id)
    filepath = os.path.join(settings.BASE_DIR, movie.srt.name)
    with open(filepath, 'r') as f:
        subs = list(srt.parse(f.read()))
        try:
            results = subs[int(start_ind)-1:int(end_ind)]
        except:
            return HttpResponse('something went wrong')
    context = {}
    context['results'] = results
    context['start_ind'] = start_ind
    context['end_ind'] = end_ind
    context['movie_id'] = movie_id
    return render(request, 'trimgif/edit.html', context)

def check_result(request, task_id):
    # if request.method == "GET" or not (task_id:=request.POST.get("task_id")):
    # return JsonResponse({'nothing': 'was returned'})
    # res = AsyncResult(task_id)
    # print(res.state)
    # print(task_id, res)
    res = None

    return JsonResponse({'task_progress': res})

def submit(request):
    if request.method == "GET" or not (indices:=request.POST.getlist("indices", [])) or not (movie_id:=request.POST.get("movie", None)):
        return redirect('trimgif:search')
    captions = {key[:-8]: request.POST.get(key) for key in request.POST if "_caption" in key}
    gif_name = f'media/gifs/gif_{datetime.now().strftime("%Y%m%d_%H%M%S")}.gif'
    gif = create_gif.delay(movie_id, indices, captions, gif_name)
    return HttpResponse(f"<a href='/{gif_name}'>click</a> task id {gif.task_id}")

@shared_task(bind=True)
def create_gif(self, movie_id, indices, captions, gif_name):
    print (self.AsyncResult(self.request.id).state)
    if not indices:
        return
    movie_obj = get_object_or_404(Movie, id=movie_id)
    filepath = os.path.join(settings.BASE_DIR, movie_obj.srt.name)
    with open(filepath, 'r') as f:
        subs = list(srt.parse(f.read()))
        indices.sort()
        results = [subs[int(index)-1] for index in indices]
    clips = []
    with VideoFileClip(os.path.join(settings.BASE_DIR, movie_obj.movie.name)) as movie:
        current_index = -2
        start_time, end_time = -1, -1
        for sub in results:
            if sub.index - results[0].index > 10:
                break
            if sub.index - current_index == 1:
                clips.append(movie.subclip(str(end_time), str(sub.start)).resize(.4))
            clip = movie.subclip(str(sub.start), str(sub.end)).resize(.4)
            caption = captions[str(sub.index)]
            height = clip.h/6 if len(caption)>30 else clip.h/10
            clip_sub = TextClip(caption, method='caption', size=(clip.w, height), color='yellow', align='South', font='Helvetica-BoldOblique').set_duration(clip.duration).set_position(('center', 'bottom'))
            clips.append(CompositeVideoClip([clip, clip_sub]))
            start_time, end_time = sub.start, sub.end
            current_index = sub.index
        final_clip = concatenate_videoclips(clips)
        final_clip.write_gif(os.path.join(settings.BASE_DIR, gif_name), fps=10)
    return '/'+gif_name

def search(request):
    results = []
    if request.method == "GET" and (query:=request.GET.get("query", None)):
        for movie in Movie.objects.all():
            filepath = os.path.join(settings.BASE_DIR, movie.srt.name)
            with open(filepath, 'r') as f:
                subs = list(srt.parse(f.read()))
                param = 2
                delta = 10
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
